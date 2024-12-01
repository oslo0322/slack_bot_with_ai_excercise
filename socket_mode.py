import json
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


def ack(req, client):
    response = SocketModeResponse(envelope_id=req.envelope_id)
    client.send_socket_mode_response(response)


def summary_thead(slack_web_client, channel, thread_ts):
    app = SlackApp(channel=channel, client=slack_web_client)
    history = app.fetch_thread_conversation_history(thread_ts)
    serialized_history = app.serialize_conversation_history(history)
    gs = GeminiService()
    gs.setup()
    return gs.generate_content("Summarize the conversation", serialized_history)


def get_command(state_values: dict):
    for k in state_values.keys():
        if "type" in state_values and "value" in state_values:
            return state_values["value"]
        else:
            return get_command(state_values[k])


def query_message(slack_web_client, channel, thread_ts, command):
    app = SlackApp(channel=channel, client=slack_web_client)
    history = app.fetch_thread_conversation_history(thread_ts)
    serialized_history = app.serialize_conversation_history(history)
    gs = GeminiService()
    gs.setup()
    result = gs.generate_content(command, serialized_history)
    print(result)
    return result


def process2(client: SocketModeClient, req: SocketModeRequest):
    print(req.type, req.payload.get("type"))

    if req.type == "interactive" and req.payload.get("type") == "message_action":
        if req.payload["callback_id"] == "summary_thread":
            ack(req, client)
            result = summary_thead(
                client.web_client,
                req.payload["channel"]["id"],
                req.payload["message"]["thread_ts"],
            )
            client.web_client.chat_postMessage(
                channel=req.payload["channel"]["id"],
                thread_ts=req.payload["message"]["thread_ts"],
                text=result,
            )
        if req.payload["callback_id"] == "query_command":
            ack(req, client)

            # Open a welcome modal
            # print(json.dumps(req.payload, indent=2))
            channel_id = req.payload["channel"]["id"]
            message = req.payload["message"]["text"]
            message_ts = req.payload["message"]["ts"]
            thread = req.payload["message"].get("thread_ts")
            metadata = {
                "channel_id": channel_id,
                "message_text": message,
                "message_ts": message,
                "thread_ts": thread,
            }
            client.web_client.views_open(
                trigger_id=req.payload["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "query-modal",
                    "title": {"type": "plain_text", "text": "Shit!"},
                    "submit": {"type": "plain_text", "text": "submit"},
                    "private_metadata": json.dumps(metadata),
                    "blocks": [
                        {
                            "type": "input",
                            "element": {"type": "plain_text_input"},
                            "label": {
                                "type": "plain_text",
                                "text": "Test",
                                "emoji": True,
                            },
                            "hint": {
                                "type": "plain_text",
                                "text": "Please enter command you want to ask with AI",
                                "emoji": True,
                            },
                        }
                    ],
                },
            )

    if req.type == "interactive" and req.payload.get("type") == "view_submission":
        if req.payload["view"]["callback_id"] == "query-modal":
            # Acknowledge the request and close the modal
            ack(req, client)
            command = ""

            try:
                command = get_command(req.payload["view"]["state"]["values"])
                print(command)
            except Exception as e:
                print(e)

            load_private_metadata = json.loads(req.payload["view"]["private_metadata"])
            # print(load_private_metadata)
            result = query_message(
                client.web_client,
                load_private_metadata["channel_id"],
                load_private_metadata["thread_ts"],
                command=command,
            )
            client.web_client.chat_postEphemeral(
                channel=load_private_metadata["channel_id"],
                thread_ts=load_private_metadata["thread_ts"],
                user=req.payload["user"]["id"],
                text=result,
            )


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
