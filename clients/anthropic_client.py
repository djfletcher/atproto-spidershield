
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
            self._client = anthropic.Anthropic()
        return self._client

    def phone_claude(self, image_data: bytes, media_type: str):
        if media_type not in SUPPORTED_MEDIA_TYPES:
            print(f"Skipping because {media_type} is not a supported media type")

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
                                "data": image_data,
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
