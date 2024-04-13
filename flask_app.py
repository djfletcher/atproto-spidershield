import logging
import os

import libipld
from flask import Flask, Response, request
from kafka import TopicPartition

from clients.kafka_client import KafkaClient

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/xrpc/com.atproto.label.subscribeLabels")
def subscribe_labels():
    """
    From here: https://github.com/bluesky-social/atproto/blob/main/lexicons/com/atproto/label/subscribeLabels.json

    Subscribe to stream of labels (and negations). Public endpoint implemented by mod services.
    Uses same sequencing scheme as repo event stream.

    :required param int cursor: the last known event seq number to backfill from
    :returns labels:
        {
            "seq": int,
            "labels": [com.atproto.Label]
        }
    OR
    :returns info:
        {
            "name": "OutdatedCursor",
            "message": str
        }
    """
    try:
        post_labels_topic = os.getenv("POST_LABELS_TOPIC")
        if not post_labels_topic:
            logging.exception(
                f"No post_labels_topic has been defined: '{post_labels_topic}'"
            )
        kafka_consumer = KafkaClient().consumer()
        topic_partition = TopicPartition(
            topic=post_labels_topic, partition=0
        )  # single partition topic for now
        kafka_consumer.assign([topic_partition])

        cursor = request.args.get("cursor")
        # TODO: look into injecting the kafka client directly into the route
        if cursor is not None:
            try:
                cursor = int(cursor)
                # in case they sent a negative cursor value
                cursor = max(cursor, 0)
            except ValueError:
                return f"Invalid cursor '{cursor}'", 400

            # verify their requested offset is not less than the max allowed lookback
            offsets = kafka_consumer.end_offsets([topic_partition])
            next_offset = offsets[topic_partition]
            max_allowed_lookback = int(
                os.getenv("SUBSCRIBE_LABELS_CURSOR_MAX_ALLOWED_LOOKBACK", 0)
            )
            if cursor < next_offset - max_allowed_lookback:
                response = {
                    "name": "OutdatedCursor",
                    "message": f"Requested cursor '{cursor}' is more than max allowed backfill of {max_allowed_lookback} behind current seq {next_offset}",
                }
                return libipld.encode_dag_cbor(response), 400
            kafka_consumer.seek(topic_partition, cursor)

        def generate():
            for message in kafka_consumer:
                block = {
                    "seq": message.offset,
                    "labels": [message.value],
                }
                yield libipld.encode_dag_cbor(block)

            kafka_consumer.close()

        return Response(generate(), mimetype="text/event-stream")
    except Exception as e:
        logging.exception(e)
        return "Internal Error", 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
