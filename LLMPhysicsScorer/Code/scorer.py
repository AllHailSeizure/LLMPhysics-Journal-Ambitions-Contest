import os
from dotenv import load_dotenv
import anthropic
from openai import OpenAI

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_connections():
    print("Testing Anthropic...")
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello in one word."}]
    )
    print("Anthropic OK:", response.content[0].text)

    print("Testing OpenAI...")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello in one word."}]
    )
    print("OpenAI OK:", response.choices[0].message.content)

test_connections()