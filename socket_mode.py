import os

import dotenv
from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from threading import Event

from gemini import GeminiService
from slack import SlackApp

dotenv.load_dotenv()


def process(client: SocketModeClient, req: SocketModeRequest):
    print(req.type)
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        # Add a reaction to the message if it's a new message
        if (
            req.payload["event"]["type"] == "message"
            and req.payload["event"].get("subtype") is None
        ):
            client.web_client.reactions_add(
                name="eyes",
                channel=req.payload["event"]["channel"],
                timestamp=req.payload["event"]["ts"],
            )
    if req.type == "interactive" and req.payload.get("type") == "shortcut":
        if req.payload["callback_id"] == "hello-shortcut":
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            # Open a welcome modal
            client.web_client.views_open(
                trigger_id=req.payload["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "hello-modal",
                    "title": {"type": "plain_text", "text": "Greetings!"},
                    "submit": {"type": "plain_text", "text": "Good Bye"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": "Hello!"},
                        }
                    ],
                },
            )

    if req.type == "interactive" and req.payload.get("type") == "view_submission":
        if req.payload["view"]["callback_id"] == "hello-modal":
            # Acknowledge the request and close the modal
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)


def summary_history(slack_web_client, channel):
    app = SlackApp(channel=channel, client=slack_web_client)
    history = app.fetch_one_day_conversation_history()
    serialized_history = app.serialize_conversation_history(history)
    print(serialized_history)
    gs = GeminiService()
    gs.setup()
    result = gs.generate_content("Summarize the conversation", serialized_history)
    print(result)
    return result


def process2(client: SocketModeClient, req: SocketModeRequest):
    print(req.type, req.payload.get("type"), req.payload["callback_id"])
    if req.type == "events_api":
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        # Add a reaction to the message if it's a new message
        if (
            req.payload["event"]["type"] == "message"
            and req.payload["event"].get("subtype") is None
        ):
            client.web_client.reactions_add(
                name="eyes",
                channel=req.payload["event"]["channel"],
                timestamp=req.payload["event"]["ts"],
            )

    if req.type == "interactive" and req.payload.get("type") == "shortcut":
        if req.payload["callback_id"] == "hello-shortcut":
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            # Open a welcome modal
            # print(req.payload["event"]["channel"])
            response = client.web_client.chat_postMessage(
                channel="C0833KTP9NV",
                text="Hello! I'm here to help you summarize the conversation.",
            )

            client.web_client.chat_update(
                channel="C0833KTP9NV",
                ts=response["ts"],
                text=summary_history(
                    slack_web_client=client.web_client,
                    channel="C0833KTP9NV",
                ),
            )

    if req.type == "interactive" and req.payload.get("type") == "view_submission":
        if req.payload["view"]["callback_id"] == "hello-modal":
            # Acknowledge the request and close the modal
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)


def main():
    # Initialize SocketModeClient with an app-level token + WebClient
    client = SocketModeClient(
        # This app-level token will be used only for establishing a connection
        app_token=os.environ["SLACK_APP_TOKEN"],  # xapp-A111-222-xyz
        # You will be using this WebClient for performing Web API calls in listeners
        web_client=WebClient(token=os.environ["SLACK_BOT_TOKEN"]),  # xoxb-111-222-xyz
    )

    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    client.socket_mode_request_listeners.append(process2)
    # Establish a WebSocket connection to the Socket Mode servers
    client.connect()
    # Just not to stop this process

    Event().wait()


if __name__ == "__main__":
    main()
