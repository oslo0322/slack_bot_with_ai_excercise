import os

import dotenv
import google.generativeai as genai

from basic import ServiceInterface

dotenv.load_dotenv()


class GeminiService(ServiceInterface):

    def setup(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-1.5-flash")

    def generate_content(self, instruction: str, conversation: list) -> str:
        inputs = instruction + "".join(conversation)
        return self.service.generate_content(inputs).text
