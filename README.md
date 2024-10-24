# Flask Kafka Agent Demo
This is a Flask-based web application integrated with Kafka for real-time messaging. The app allows users to input observations, which are processed by a trained AI agent, and then returns an action based on the input. The interaction between the Flask app and Kafka uses producer-consumer messaging to demonstrate a distributed and scalable architecture.

## Features
- Flask-based API to handle observations and produce them to Kafka.
- Kafka consumer integrated with a trained AI agent to generate actions based on incoming observations.
- Dockerized setup for easy deployment, including Kafka, Zookeeper, and Flask.
- Logging integrated for real-time monitoring of Kafka messages.

## Project Structure
```bash
├── Dockerfile                 # Dockerfile for building the Flask app container
├── model/agent.json           # Trained Agent file
├── agent_inference.py         # Main Flask app that handles inference, Kafka producer, and consumer logic
├── kafka_random_producer.py   # Script for generating random observations and sending them to Kafka
├── requirements.txt           # Python dependencies
├── .env                       # Environment file (contains sensitive keys and configuration)
├── docker-compose.yml         # Docker Compose for running Flask, Kafka, Zookeeper, and other components
└── README.md                  
```

## Requirements
- Docker
- Python 3.10.x

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/composabl/agent-kafka-app.git
cd agent-kafka-app
```

### 2. Build the Docker Images
To build the Docker images for all the services defined in Docker Compose, run:
```sh
docker-compose build
```

### 3. Run the Application
After building the Docker images, start all the services:
```sh
docker-compose up -d
```
This will start the following services:
- **Zookeeper**: Manages Kafka brokers.
- **Kafka**: Messaging broker.
- **Flask App**: The main application to interact with the AI agent.
- **Kafdrop**: UI tool for monitoring Kafka topics.

The Flask app will be available at [http://localhost:8000](http://localhost:8000).

### 4. Environment Variables
Ensure that you add the required environment variables in the `.env` file:
```env
COMPOSABL_LICENSE=your_license_key_here
KAFKA_BROKER_URL=kafka:9092
OBSERVATION_TOPIC=observations
ACTION_TOPIC=actions
```

## Accessing the App
### Flask API Endpoint
- **/predict**: This endpoint accepts observation data and sends it to Kafka.
  - Example usage with `curl`:
  ```sh
  curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{
    "observation": {
      "T": 311.0,
      "Tc": 292.0,
      "Ca": 8.56,
      "Cref": 8.56,
      "Tref": 311.0,
      "Conc_Error": 0.0,
      "Eps_Yield": 0.0,
      "Cb_Prod": 0.0
    }
  }'
  ```
- **Kafka Consumer**: The consumer thread runs automatically in the Flask app and processes messages from the `observations` topic to generate actions.

### Using Kafdrop to Monitor Kafka
Kafdrop is accessible at [http://localhost:9000](http://localhost:9000). Use it to:
- View topics (`observations`, `actions`).
- Inspect message flow and verify that observations are being produced and actions are generated.

## Running the Random Observation Generator
The `kafka_random_producer.py` script can be run manually to generate random observations:
1. **Enter the Flask container**:
   ```sh
   docker exec -it flask_app sh
   ```
2. **Run the script**:
   ```sh
   python kafka_random_producer.py
   ```
   This will send random observations to the `observations` topic in Kafka.

## Development Setup (Without Docker)
If you prefer to run the app locally without Docker:
1. **Install the required dependencies**:
   ```sh
   pip install -r requirements.txt
   ```
2. **Start Zookeeper and Kafka** locally (you may need to install Kafka and Zookeeper manually).
3. **Run the Flask app**:
   ```sh
   python agent_inference.py
   ```
   The app will run on [http://localhost:8000](http://localhost:8000).

## Notes
- **Kafka and Zookeeper** must be running for the app to work correctly.
- **Logging** is enabled to monitor the flow of data between Kafka and Flask.
- **Flask is running in debug mode** for development purposes. Disable this in production by setting `debug=False`.

## License
Ensure you have a valid license key for the AI agent (`COMPOSABL_LICENSE`), as it is required for the app to function.

## Contributions
Feel free to contribute by submitting pull requests or opening issues!

## Troubleshooting
- If **Kafka broker is unavailable**, check that the advertised listeners are correctly set up and that the services are connected to the same Docker network.
- Use **Kafdrop** to verify message flow and **docker-compose logs** to debug issues.

