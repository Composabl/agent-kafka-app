import asyncio
import os
import threading
import signal
import sys
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from composabl import Agent, Trainer
import numpy as np
from flask import Flask, request, jsonify
import json
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

# Global objects (initialized once)
trainer = None
trained_agent = None
producer = None
consumer = None
license_key = os.getenv("COMPOSABL_LICENSE")

PATH = os.path.dirname(os.path.realpath(__file__))
PATH_CHECKPOINTS = f"{PATH}/model/agent.json"

# Kafka configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "kafka:9092")
OBSERVATION_TOPIC = os.getenv("OBSERVATION_TOPIC", "observations")
ACTION_TOPIC = os.getenv("ACTION_TOPIC", "actions")

# Initialize the runtime, load the model, and package it when the app starts
async def init_runtime():
    """
    Initializes the trainer and agent before the first request is processed.
    This sets up the AI model for inference, loading it from checkpoints and preparing the agent.
    """
    global trainer, trained_agent, producer

    # Assuming 'config' is required to initialize the Trainer
    config = {
        "license": license_key,
        "target": {
            "local": {"address": "localhost:1337"}
        },
        "env": {
            "name": "sim-deploy",
        },
        "trainer": {
            "workers": 1
        }
    }

    # Initialize the Trainer with the config
    trainer = Trainer(config)

    # Load the agent from the given checkpoint path
    agent = Agent.load(PATH_CHECKPOINTS)

    # Package the agent for inference using the Trainer's _package function (asynchronously)
    trained_agent = await trainer._package(agent)

    # Initialize Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info(f"Connected to Kafka broker at {KAFKA_BROKER_URL}")
    except KafkaError as e:
        logging.error(f"Failed to connect to Kafka broker: {e}")

# Asynchronous POST route to receive observation and send it to Kafka
@app.route('/predict', methods=['POST'])
async def predict():
    """
    Receives an observation through a POST request, processes it using Kafka,
    and returns the corresponding action.
    """
    # Extract the observation from the request's JSON body
    obs = request.json.get("observation")

    # Validate that the observation was provided in the request
    if obs is None:
        logging.error("No observation provided in the request")
        return jsonify({"error": "No observation provided"}), 400

    obs = dict(obs)

    try:
        # Send the observation to Kafka
        producer.send(OBSERVATION_TOPIC, value=obs)
        logging.info(f"Sent observation to Kafka topic '{OBSERVATION_TOPIC}': {obs}")
        return jsonify({"message": "Observation sent to Kafka"}), 200
    except KafkaError as e:
        logging.error(f"Failed to send observation to Kafka: {e}")
        return jsonify({"error": str(e)}), 500

# Function to consume messages from Kafka and process them
def consume_observations():
    """
    Consumes observations from Kafka, runs them through the trained agent, 
    and publishes the actions back to Kafka.
    """
    global trained_agent, consumer

    consumer = KafkaConsumer(
        OBSERVATION_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='agent-consumer-group'
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URL,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    for message in consumer:
        obs = message.value
        logging.info(f"Received message from Kafka topic '{OBSERVATION_TOPIC}': {obs}")
        try:
            # Convert the observation to a numpy array for sims that requires array as input
            obs_array = np.array([float(x) for x in list(obs.values())])
            # Asynchronously process the observation to generate the action
            action = asyncio.run(trained_agent._execute(obs_array))
            logging.info(f"Generated action from observation: {action}")
        except Exception as e:
            logging.error(f"Error processing observation: {e}")
            continue

        # Publish the generated action back to Kafka
        action_value = {"action": action.tolist() if isinstance(action, np.ndarray) else action}
        producer.send(ACTION_TOPIC, value=action_value)
        logging.info(f"Published action to topic '{ACTION_TOPIC}': {action_value}")

# Signal handler to gracefully shut down Kafka consumer and producer
def shutdown_handler(signum, frame):
    global producer, consumer
    if producer is not None:
        producer.close()
        logging.info("Kafka producer closed successfully")
    if consumer is not None:
        consumer.close()
        logging.info("Kafka consumer closed successfully")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handling to gracefully shut down
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Run the Flask application with async support on localhost, port 8000
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_runtime())

    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_observations)
    consumer_thread.start()

    # Run Flask app
    app.run(host="0.0.0.0", port=8000, debug=True)