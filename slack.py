import logging


import os
from datetime import date, datetime, timedelta

import dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackApp:
    def __init__(self, channel: str, client: WebClient | None = None):
        dotenv.load_dotenv()
        self.client = client or WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        self.channel = channel

    def fetch_conversation_history(
        self, start_timestamp: float | None = None, end_timestamp: float | None = None
    ):
        kwargs = {}
        if start_timestamp:
            kwargs["oldest"] = str(start_timestamp)
        if end_timestamp:
            kwargs["latest"] = str(end_timestamp)
        try:
            response = self.client.conversations_history(channel=self.channel, **kwargs)
            return response
        except SlackApiError as e:
            assert e.response["error"]

    def fetch_one_day_conversation_history(self):
        end_time = datetime.combine(date.today(), datetime.min.time())
        start_time = end_time - timedelta(days=1)
        return self.fetch_conversation_history(
            start_timestamp=start_time.timestamp(), end_timestamp=end_time.timestamp()
        )

    @staticmethod
    def serialize_conversation_history(conversation_history):
        return [
            f"@{message.get('user', '')}: {message.get('text', '')}"
            for message in conversation_history.get("messages")
            if message.get("type") == "message"
        ]


if __name__ == "__main__":
    app = SlackApp(channel="C0833KTP9NV")
    history = app.fetch_one_day_conversation_history()
    serialized_history = app.serialize_conversation_history(history)
    print(serialized_history)
