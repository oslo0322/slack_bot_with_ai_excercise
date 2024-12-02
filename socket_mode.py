import os
from threading import Event

import dotenv
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.listeners import SocketModeRequestListener
from slack_sdk.web import WebClient

from gemini import GeminiService
from listeners import MySocketModeRequestListener

dotenv.load_dotenv()


def main():
    # Initialize SocketModeClient with an app-level token + WebClient
    client = SocketModeClient(
        # This app-level token will be used only for establishing a connection
        app_token=os.environ["SLACK_APP_TOKEN"],  # xapp-A111-222-xyz
        # You will be using this WebClient for performing Web API calls in listeners
        web_client=WebClient(token=os.environ["SLACK_BOT_TOKEN"]),  # xoxb-111-222-xyz
    )
    llm_service = GeminiService()
    llm_service.setup()
    request_listener: SocketModeRequestListener = MySocketModeRequestListener(
        llm_service=llm_service
    )
    # Add a new listener to receive messages from Slack
    # You can add more listeners like this
    client.socket_mode_request_listeners.append(request_listener)
    # Establish a WebSocket connection to the Socket Mode servers
    client.connect()
    # Just not to stop this process
    Event().wait()


if __name__ == "__main__":
    main()
