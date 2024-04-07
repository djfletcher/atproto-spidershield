import base64
from datetime import datetime
from typing import List, Tuple

from atproto_client.client.raw import ClientRaw
from atproto_client.models.app.bsky.embed.images import Image
from atproto_client.models.com.atproto.label.defs import Label
from atproto_client.namespaces.sync_ns import ComAtprotoSyncNamespace

from clients.anthropic_client import AnthropicClient
from clients.kafka_client import KafkaClient
from utils.atproto_utils import get_post_url


class Labeler:
    def __init__(self, post_labels_topic: str, image_labels_topic: str):
        self._kafka_client = None
        self._anthropic_client = None
        self._raw_client = None
        self._sync_namespace = None

        if not post_labels_topic:
            raise ValueError("No post labels topic was provided")
        if not image_labels_topic:
            raise ValueError("No image labels topic was provided")

        self.post_labels_topic = post_labels_topic
        self.image_labels_topic = image_labels_topic

    @property
    def kafka_client(self):
        if self._kafka_client is None:
            self._kafka_client = KafkaClient()
        return self._kafka_client

    @property
    def anthropic_client(self):
        if self._anthropic_client is None:
            self._anthropic_client = AnthropicClient()
        return self._anthropic_client

    @property
    def raw_client(self):
        if self._raw_client is None:
            self._raw_client = ClientRaw()
        return self._raw_client

    @property
    def sync_namespace(self):
        if self._sync_namespace is None:
            self._sync_namespace = ComAtprotoSyncNamespace(self.raw_client)
        return self._sync_namespace

    def maybe_label_post(self, post: dict):
        """
        TODO: docs
        """
        embed = post["record"].embed
        if embed and hasattr(embed, "images") and embed.images:
            decisions = []
            for idx, image in enumerate(embed.images, start=1):
                print(f"Processing image {idx} of {len(embed.images)} images")
                claude_response = self.process_image(image, post["author"])
                content = claude_response.content[0]
                post_url = get_post_url(post)
                print("================================")
                print(
                    f"""
    CLAUDE SAYS: '{content.text}'
    FOR POST: {post_url}
    """
                )
                print("================================")
                decisions.append((image, content.text))
            self.publish_labels(decisions, post)

    def publish_labels(self, decisions: List[Tuple[Image, str]], post: dict):
        """
        TODO: docs
        """
        print(f"Processing {len(decisions)} decisions")
        for image, decision in decisions:
            created_at = datetime.now()
            post_label = self.make_post_label(post, decision, created_at)
            self.kafka_client.producer.send(
                self.post_labels_topic, key=post["cid"], value=post_label
            )
            blob_cid = image.image.cid
            image_cid = blob_cid._cid
            image_label = self.make_image_label(
                image_cid, post["uri"], post["author"], decision, created_at
            )
            self.kafka_client.producer.send(
                self.image_labels_topic, key=image_cid, value=image_label
            )

    def process_image(self, image: Image, author_did: str):
        """
        Example image:
            {'alt': '',
             'aspect_ratio': {'height': 1613,
                              'py_type': 'app.bsky.embed.images#aspectRatio',
                              'width': 1613},
             'image': {'mime_type': 'image/jpeg',
                       'py_type': 'blob',
                       'ref': 'bafkreicla36qauuuylngywjsjb3bztqt7msknfenlucuegl4objslujgjm',
                       'size': 624777},
             'py_type': 'app.bsky.embed.images#image'}
        """
        blob_cid = image.image.cid
        downloaded_blob = self.sync_namespace.get_blob(
            {"cid": blob_cid._cid, "did": author_did}
        )
        decoded_blob = base64.b64encode(downloaded_blob).decode("utf-8")
        return self.anthropic_client.phone_claude(decoded_blob, image.image.mime_type)

    @staticmethod
    def make_post_label(post: dict, val: str, created_at: datetime) -> Label:
        """
        https://docs.bsky.app/docs/advanced-guides/moderation

        example label:
        {
          /** DID of the actor who created this label. */
          src: string
          /** AT URI of the record, repository (account), or other resource that this label applies to. */
          uri: string
          /** Optionally, CID specifying the specific version of 'uri' resource this label applies to. */
          cid?: string
          /** The short string name of the value or type of this label. */
          val: string
          /** If true, this is a negation label, overwriting a previous label. */
          neg?: boolean
          /** Timestamp when this label was created. */
          cts: string
        }

        example post:
        {'author': 'did:plc:ghrlooc6r56in4d7n6ljr7qt',
         'cid': 'bafyreidaxqdy72piowe4csqnty7rvt4jh6sdu62i3gzaqia3afizldpfvi',
         'record': Record(created_at='2024-03-18T23:02:46.310Z', text='contra dance confusion', embed=Main(images=[Image(alt='', image=BlobRef(mime_type='image/jpeg', size=624777, ref='bafkreicla36qauuuylngywjsjb3bztqt7msknfenlucuegl4objslujgjm', py_type='blob'), aspect_ratio=AspectRatio(height=1613, width=1613, py_type='app.bsky.embed.images#aspectRatio'), py_type='app.bsky.embed.images#image')], py_type='app.bsky.embed.images'), entities=None, facets=None, labels=None, langs=['en'], reply=None, tags=None, py_type='app.bsky.feed.post'),
         'uri': 'at://did:plc:ghrlooc6r56in4d7n6ljr7qt/app.bsky.feed.post/3knyxhlml3i2x'}
        """
        return Label(
            src=post["author"],
            uri=post["uri"],
            cid=post["cid"],
            val=val,
            neg=False,
            cts=created_at.isoformat(),
        )

    @staticmethod
    def make_image_label(
        image_cid: str, uri: str, author_did: str, val: str, created_at: datetime
    ) -> Label:
        """
        example image:
        {'alt': '',
         'aspect_ratio': {'height': 1613,
                          'py_type': 'app.bsky.embed.images#aspectRatio',
                          'width': 1613},
         'image': {'mime_type': 'image/jpeg',
                   'py_type': 'blob',
                   'ref': 'bafkreicla36qauuuylngywjsjb3bztqt7msknfenlucuegl4objslujgjm',
                   'size': 624777},
         'py_type': 'app.bsky.embed.images#image'}
        """
        return Label(
            src=author_did,
            # TODO: Verify that the uri of the blob should be the same as the post's (since they live in the same commit block)
            uri=uri,
            cid=image_cid,
            val=val,
            neg=False,
            cts=created_at.isoformat(),
        )
