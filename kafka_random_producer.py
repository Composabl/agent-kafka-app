from kafka import KafkaProducer
import json
import random
import time

# Kafka configuration
KAFKA_BROKER_URL = "kafka:9092"
OBSERVATION_TOPIC = "agent_input"

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_random_observation():
    # Generate a random observation
    observation = {
        "T": random.uniform(200.0, 420.0),
        "Tc": random.uniform(180.0, 300.0),
        "Ca": random.uniform(5.0, 10.0),
        "Cref": random.uniform(3.0, 15.0),
        "Tref": random.uniform(250.0, 320.0),
        "Conc_Error": random.uniform(0.0, 10.0),
        "Eps_Yield": random.uniform(0.0, 50.0),
        "Cb_Prod": random.uniform(0.0, 10.0)
    }
    return observation

# Produce random observations in a loop
if __name__ == "__main__":
    while True:
        observation = generate_random_observation()
        producer.send(OBSERVATION_TOPIC, value=observation)
        print(f"Sent observation to Kafka topic '{OBSERVATION_TOPIC}': {observation}")
        time.sleep(2)  # Send every 2 seconds
