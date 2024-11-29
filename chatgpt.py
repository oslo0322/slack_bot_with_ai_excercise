import dotenv
from openai import OpenAI

dotenv.load_dotenv()
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about recursion in programming."},
    ],
)
print(completion.usage)

print(completion.choices[0].message)
