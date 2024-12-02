import json

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from slack import SlackApp


class MySocketModeRequestListener:

    def __init__(self, llm_service):
        self.llm_service = llm_service

    @staticmethod
    def ack(req, client):
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

    def summary_thead(self, slack_web_client, channel, thread_ts):
        app = SlackApp(channel=channel, client=slack_web_client)
        history = app.fetch_thread_conversation_history(thread_ts)
        serialized_history = app.serialize_conversation_history(history)
        return self.llm_service.generate_content(
            "Summarize the conversation", serialized_history
        )

    def get_command(self, state_values: dict):
        for k in state_values.keys():
            if "type" in state_values and "value" in state_values:
                return state_values["value"]
            else:
                return self.get_command(state_values[k])

    def query_message(self, slack_web_client, channel, thread_ts, command):
        app = SlackApp(channel=channel, client=slack_web_client)
        history = app.fetch_thread_conversation_history(thread_ts)
        serialized_history = app.serialize_conversation_history(history)
        result = self.llm_service.generate_content(command, serialized_history)
        return result

    def __call__(self, client: SocketModeClient, req: SocketModeRequest):
        print(req.type, req.payload.get("type"))

        if req.type == "interactive" and req.payload.get("type") == "message_action":
            if req.payload["callback_id"] == "summary_thread":
                self.ack(req, client)
                result = self.summary_thead(
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
                self.ack(req, client)

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
                self.ack(req, client)
                command = ""

                try:
                    command = self.get_command(req.payload["view"]["state"]["values"])
                    print(command)
                except Exception as e:
                    print(e)

                load_private_metadata = json.loads(
                    req.payload["view"]["private_metadata"]
                )
                # print(load_private_metadata)
                result = self.query_message(
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
