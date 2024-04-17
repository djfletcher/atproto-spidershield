## Spider Shield

🚧 Under Construction 🚧

An AT protocol labeling service that blocks photos of spiders from your Bluesky experience. Operated by [@flaniel.bsky.social](https://bsky.app/profile/flaniel.bsky.social), and inspired by the moderation example from [Bluesky’s Stackable Approach to Moderation](https://bsky.social/about/blog/03-12-2024-stackable-moderation), this service consumes from the Bluesky firehose and forwards new images to Anthropic's [Messages API](https://docs.anthropic.com/claude/docs/vision#3-example-multiple-images-with-a-system-prompt) to get a yes/no verdict on whether each image contains a spider.

## Next Up
- Ingest firehose using multi-processing

## Setup Instructions
Paste in your Anthropic API key into a file called build/anthropic_api_key.txt. This will get pulled into docker as secret. Generate an API key by following these steps: https://docs.anthropic.com/claude/docs/getting-access-to-claude#step-3-generate-an-api-key
```
echo -n "<your key here>" > build/anthropic_api_key.txt
```

Make sure you keep these keys secret:
```
chmod 600 build/anthropic_api_key.txt  # restrict permissions so that only you can read the file
```

Export environment variables in current terminal session:
```
source .env
```

Build docker images:
```
docker build -f build/firehose_ingest.Dockerfile -t bluesky-firehose-ingest .
docker build -f build/flask_app.Dockerfile -t spidershield-api .
```

Start docker containers:
```
docker compose -p atproto-spidershield up -d
```

To subscribe to labels via http:
```
# by default it will subscribe starting with new labels
curl http://localhost:5001/xrpc/com.atproto.label.subscribeLabels --no-buffer --output -

# or give it a specific cursor location to start from
curl http://localhost:5001/xrpc/com.atproto.label.subscribeLabels\?cursor\=1000 --no-buffer --output -
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