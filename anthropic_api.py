import os
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def invoke_anthropic_api(conversation_history, model, temperature, system_message):
    client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=model,
        messages=conversation_history,
        max_tokens=4096,
        temperature=temperature,
        system=system_message,
    )

    content_text = " ".join(block.text for block in response.content)
    return content_text
