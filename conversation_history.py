import os
import sys
import json

CURRENT_CONVERSATION_FILE = "current_conversation.txt"
CONVERSATIONS_DIRECTORY = os.path.expanduser("~/conversations")


def save_conversation_history(conversation_history, file_path):
    with open(file_path, "w") as file:
        json.dump(conversation_history, file)


def load_conversation_history(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def get_current_conversation_file():
    try:
        with open(CURRENT_CONVERSATION_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def set_current_conversation_file(file_name):
    with open(CURRENT_CONVERSATION_FILE, "w") as file:
        file.write(file_name)


def reset_conversation():
    current_conversation_file = get_current_conversation_file()
    if current_conversation_file:
        set_current_conversation_file("")
    print("Conversation reset.", file=sys.stderr)
