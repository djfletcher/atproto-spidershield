## Setup Instructions
Copy the `build/.env.template` file to a new `.env` file:
```
cp build/.env.template .env
```


Update the `.env` with your Anthropic API key by following these steps: https://docs.anthropic.com/claude/docs/getting-access-to-claude#step-3-generate-an-api-key
```
ANTHROPIC_API_KEY=<your key here>
```

Make sure you keep these keys secret:
```
chmod 600 .env  # restrict permissions so that only you can read the file
```

Export environment variables in current terminal session:
```
source .env
```

Build docker images and start the containers:
```
docker build -f build/firehose_ingest.Dockerfile -t firehose-ingest .
docker build -f build/flask_app.Dockerfile -t flask-app .
docker compose -p atproto-spidershield up -d
```

To subscribe to labels via http:
```
# by default it will subscribe starting with new labels
curl http://localhost:5001/xrpc/com.atproto.label.subscribeLabels --no-buffer

# or give it a specific cursor location to start from
curl http://localhost:5001/xrpc/com.atproto.label.subscribeLabels\?cursor\=1000 --no-buffer
```

To consume from kafka directly, exec into the kafka docker container and run this command:
```
opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test_post_labels --from-beginning
```

To run the linters:
```
source venv/bin/activate
pip install -r dev-requirements.txt

# run black
python -m black . --verbose --color

# run isort
python -m isort . --color -s venv -s __init__.py -p test

# flake
python -m autoflake --in-place -r . --exclude venv --remove-all-unused-imports

# mypy
python -m mypy --no-strict-optional -p .
```