import os

from atproto import (FirehoseSubscribeReposClient, models,
                     parse_subscribe_repos_message)

from labeler import Labeler
from utils.atproto_utils import get_ops_by_type


def label_posts_in_commit(message) -> None:
    post_labels_topic = os.getenv("POST_LABELS_TOPIC")
    image_labels_topic = os.getenv("IMAGE_LABELS_TOPIC")
    labeler = Labeler(post_labels_topic, image_labels_topic)

    commit = parse_subscribe_repos_message(message)
    if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
        return

    if not commit.blocks:
        return

    ops = get_ops_by_type(commit)
    for post in ops["posts"]["created"]:
        post_msg = post["record"].text
        post_langs = post["record"].langs
        print(f"Handling post in {post_langs}: {post_msg}")
        labeler.maybe_label_post(post)


if __name__ == "__main__":
    """
    Example command:
    python -m firehose
    """
    client = FirehoseSubscribeReposClient()
    client.start(label_posts_in_commit)
