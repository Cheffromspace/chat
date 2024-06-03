import os
import json
import argparse
from colorama import init, Fore, Style, Back
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CURRENT_CONVERSATION_FILE = "current_conversation.txt"
CONVERSATIONS_DIRECTORY = os.path.expanduser("~/conversations")
DEFAULT_SYSTEM_MESSAGE = """
1. Acknowledge the user's technical expertise and problem-solving skills.

2. Provide clear, concise, and relevant information when discussing issues and solutions.

3. Listen attentively to the user's concerns, questions, and ideas.

4. Offer proactive insights, suggestions, and alternative perspectives to help identify and resolve issues.

5. Celebrate the user's progress and successful implementation of fixes.

6. Foster a collaborative environment that values open communication and the sharing of ideas.

7. Adapt communication style to match the user's preferences and maintain productivity.

8. Continuously learn from the user's expertise and incorporate their feedback.

9. Maintain a strong commitment to the user's success and satisfaction.

By following these guidelines, you can provide an effective, efficient, and professional troubleshooting collaboration experience tailored to the user's needs."
"""


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


def generate_conversation_name(first_message):
    client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "user",
                "content": f"Summarize the following message in 10 words or fewer. Use no punctuation. Return alphanumeric charachters and spaces only: {first_message}",
            }
        ],
        max_tokens=50,
        temperature=0.7,
        system="Generate a concise summary of the given message.",
    )

    content_text = " ".join(block.text for block in response.content)
    print_colored(f"Title: {content_text}", fore_color=Fore.GREEN)
    conversation_name = content_text.replace(" ", "_").replace(".", "")
    return conversation_name


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


def invoke_conversation(
    message,
    model="claude-3-opus-20240229",
    temperature=0.7,
    system_message=DEFAULT_SYSTEM_MESSAGE,
):
    current_conversation_file = get_current_conversation_file()

    if not current_conversation_file:
        conversation_name = generate_conversation_name(message)
        current_conversation_file = f"{conversation_name}.json"
        set_current_conversation_file(current_conversation_file)
    conversation_history = load_conversation_history(
        os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file)
    )
    conversation_history.append({"role": "user", "content": message})

    assistant_response = invoke_anthropic_api(
        conversation_history, model, temperature, system_message
    )

    conversation_history.append({"role": "assistant", "content": assistant_response})

    save_conversation_history(
        conversation_history,
        os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file),
    )

    return "assistant", assistant_response


def reset_conversation():
    current_conversation_file = get_current_conversation_file()
    if current_conversation_file:
        os.remove(os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file))
        set_current_conversation_file("")
    print("Conversation reset.")


init()  # Initialize colorama


def print_colored(
    text, fore_color=Fore.RESET, back_color=Back.RESET, style=Style.NORMAL
):
    print(f"{fore_color}{back_color}{style}{text}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(description="Anthropic CLI")
    subparsers = parser.add_subparsers(dest="command")

    chat_parser = subparsers.add_parser(
        "chat", help="Send a message to the AI assistant"
    )
    chat_parser.add_argument("message", type=str, help="The message to send")

    reset_parser = subparsers.add_parser("reset", help="Reset the conversation history")

    write_parser = subparsers.add_parser(
        "write", help="Write the conversation history to a file"
    )
    write_parser.add_argument(
        "-n", "--name", type=str, help="The name of the conversation"
    )
    history_parser = subparsers.add_parser(
        "history", help="Display the conversation history"
    )

    write_parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=os.path.expanduser("~/conversations"),
        help="The directory to save the conversation file",
    )

    import_parser = subparsers.add_parser(
        "import", help="Import a conversation history from a file"
    )
    import_parser.add_argument(
        "file_path", type=str, help="The path to the conversation file"
    )

    args = parser.parse_args()

    if args.command == "chat":
        role, response = invoke_conversation(args.message)
        if role == "assistant":
            print_colored("Assistant:", fore_color=Fore.BLUE, style=Style.BRIGHT)
            print_colored(response, fore_color=Fore.BLUE, style=Style.NORMAL)
        else:
            print_colored("User:", fore_color=Fore.MAGENTA, style=Style.BRIGHT)
            print_colored(response, fore_color=Fore.MAGENTA, style=Style.NORMAL)

    elif args.command == "reset":
        reset_conversation()
    # elif args.command == "write":
    #     write_conversation(args.name, args.directory)
    # elif args.command == "import":
    #     import_conversation(args.file_path)
    elif args.command == "history":
        # display_conversation_history in a human-readable format
        print("Conversation history:")
        current_conversation_file = get_current_conversation_file()
        if current_conversation_file:
            conversation_history = load_conversation_history(
                os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file)
            )
            for message in conversation_history:
                role = message["role"]
                content = message["content"]
                if role == "assistant":
                    print_colored(
                        "Assistant:", fore_color=Fore.BLUE, style=Style.BRIGHT
                    )
                    print_colored(content, fore_color=Fore.BLUE, style=Style.NORMAL)
                else:
                    print_colored("User:", fore_color=Fore.MAGENTA, style=Style.BRIGHT)
                    print_colored(content, fore_color=Fore.MAGENTA, style=Style.NORMAL)
                print()
                print_colored(
                    "*************", fore_color=Fore.YELLOW, style=Style.BRIGHT
                )
                print()
        else:
            print("No conversation history available.")


if __name__ == "__main__":
    main()
