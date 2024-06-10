import os
from conversation_history import (
    save_conversation_history,
    load_conversation_history,
    get_current_conversation_file,
    set_current_conversation_file,
)
from formatting import format_conversation_title
from anthropic_api import invoke_anthropic_api
from user_config import load_user_config
from system_prompts import SYSTEM_PROMPTS


def invoke_conversation(
    message,
    model=None,
    temperature=None,
    system_message=None,
    conversations_directory=None,
):
    current_conversation_file = get_current_conversation_file()

    if not current_conversation_file:
        conversation_name = generate_conversation_name(message)
        current_conversation_file = f"{conversation_name}.json"
        set_current_conversation_file(current_conversation_file)
        save_conversation_history([])

    user_config = load_user_config()
    model = model or user_config["model"]
    temperature = temperature or user_config["temperature"]
    system_message = system_message or SYSTEM_PROMPTS[user_config["persona"]]
    conversations_directory = (
        conversations_directory or user_config["conversations_directory"]
    )

    conversation_history = load_conversation_history()
    conversation_history.append({"role": "user", "content": message})

    assistant_response = invoke_anthropic_api(
        conversation_history, model, temperature, system_message
    )

    conversation_history.append({"role": "assistant", "content": assistant_response})

    save_conversation_history(conversation_history)

    return "assistant", assistant_response


def generate_conversation_name(first_message):
    conversation_history = [
        {
            "role": "user",
            "content": f"<instructions>Summarize the following message in 10 words or fewer. Use no punctuation. Focus on the user's instructions, pay less attention to code snippets. This will be used to create a file name so please create a memorable title in a suitable format. Return alphanumeric characters and spaces only. Don't reference the instructions within these tags:</instructions>\n\n<first_message>{first_message}</first_message>",
        }
    ]

    content_text = invoke_anthropic_api(
        conversation_history,
        model="claude-3-haiku-20240307",
        temperature=0.7,
        system_message="Generate a concise summary of the given message.",
    )
    truncated_message = content_text[:100]
    format_conversation_title(truncated_message)
    conversation_name = truncated_message.replace(" ", "_").replace(".", "")
    return conversation_name


def get_conversation_names():
    conversations_directory = load_user_config()["conversations_directory"]
    conversation_files = os.listdir(conversations_directory)
    conversation_names = [
        file_name[:-5]
        for file_name in conversation_files
        if file_name.endswith(".json")
    ]
    return conversation_names


def remove_last_interaction():
    current_conversation_file = get_current_conversation_file()
    if current_conversation_file:
        conversation_history = load_conversation_history()
        if len(conversation_history) >= 2:
            conversation_history = conversation_history[:-2]
            save_conversation_history(conversation_history)
            return True
        else:
            return False
    else:
        return False
