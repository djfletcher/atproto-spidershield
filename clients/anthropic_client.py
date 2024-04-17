import logging
from io import BytesIO
from PIL import Image

import anthropic

HAIKU_MODEL_NAME = "claude-3-haiku-20240307"

SUPPORTED_MEDIA_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]


SYSTEM_PROMPT = """
You are being used as a moderation tool for a social network. The goal is to protect users from seeing images of spiders, because spiders are unpleasant to look at. You will be shown an image, and you will respond with a single word "yes" or "no" indicating whether the image contains a spider.

Example 1:
[User]: Does this image contain a spider? Respond with a single word "Yes" or "No".
[Assistant]: Yes

Example 2:
[User]: Does this image contain a spider? Respond with a single word "Yes" or "No".
[Assistant]: No
"""

USER_PROMPT = (
    'Does this image contain a spider? Respond with a single word "Yes" or "No".'
)


class AnthropicClient:

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                with open("/run/secrets/anthropic_api_key") as f:
                    anthropic_api_key = f.read()
                    self._client = anthropic.Anthropic(api_key=anthropic_api_key)
            except Exception as e:
                logging.exception("Failed to load anthropic api key from file")
        return self._client

    @staticmethod
    def compress_image(image_data: str, media_type: str) -> bytes:
        # turn "image/jpeg" into "JPEG", which is expected by Pillow
        img_format = media_type.split("/")[-1].upper()
        image = Image.open(BytesIO(image_data), formats=[img_format])
        compressed_image = BytesIO()
        print(f"Saving image at 50% quality")
        image.save(compressed_image, format=img_format, quality=50)  # Adjust the quality as needed
        compressed_image.seek(0)
        return compressed_image

    def phone_claude(self, image_data: str, media_type: str):
        if media_type not in SUPPORTED_MEDIA_TYPES:
            print(f"Skipping because {media_type} is not a supported media type")

        compressed_image = self.compress_image(image_data, media_type)
        print("phoning claude...")
        return self.client.messages.create(
            model=HAIKU_MODEL_NAME,
            # based on testing, 'yes' and 'no' responses take 4 tokens
            max_tokens=4,
            system=SYSTEM_PROMPT,
            # makes it more deterministic
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": compressed_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": USER_PROMPT,
                        },
                    ],
                }
            ],
        )
