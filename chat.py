import os
import json
from utils import output_json
from pathlib import Path
import argparse
import argcomplete
from rich.console import Console
from rich.table import Table
from anthropic_api import invoke_anthropic_api
from conversation_history import (
    save_conversation_history,
    load_conversation_history,
    get_current_conversation_file,
    set_current_conversation_file,
    reset_conversation,
    CONVERSATIONS_DIRECTORY,
)
from formatting import (
    format_user_message,
    format_assistant_message,
    format_conversation_title,
)
from system_prompts import SYSTEM_PROMPTS

CURRENT_CONVERSATION_FILE = "current_conversation.txt"

console = Console()


def load_user_config():
    home_dir = Path.home()
    config_file = home_dir / ".anthropic_config.json"

    if config_file.exists():
        with open(config_file, "r") as file:
            return json.load(file)
    else:
        return {
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "persona": "default",
            "conversations_directory": str(home_dir / "conversations"),
        }


def invoke_conversation(
    message, model, temperature, system_message, conversations_directory
):
    current_conversation_file = get_current_conversation_file()

    if not current_conversation_file:
        conversation_name = generate_conversation_name(message)
        current_conversation_file = f"{conversation_name}.json"
        set_current_conversation_file(current_conversation_file)

    conversation_history = load_conversation_history(
        os.path.join(conversations_directory, current_conversation_file)
    )
    conversation_history.append({"role": "user", "content": message})

    assistant_response = invoke_anthropic_api(
        conversation_history, model, temperature, system_message
    )

    conversation_history.append({"role": "assistant", "content": assistant_response})

    save_conversation_history(
        conversation_history,
        os.path.join(conversations_directory, current_conversation_file),
    )

    return "assistant", assistant_response


def generate_conversation_name(first_message):
    conversation_history = [
        {
            "role": "user",
            "content": f"""<instructions>Summarize the following message in 10 words or fewer.
Use no punctuation. Focus on the user's instructions, pay less attention to code snippets. This will be used to create a file name so please create a memorable title in a suitible format. Return alphanumeric characters and spaces only </instructions>
<message>{first_message}</message>""",
        }
    ]

    content_text = invoke_anthropic_api(
        conversation_history,
        model="claude-3-haiku-20240307",
        temperature=0.7,
        system_message="Generate a concise summary of the given message.",
    )
    format_conversation_title(content_text)
    conversation_name = content_text.replace(" ", "_").replace(".", "")
    return conversation_name


def get_conversation_names():
    conversation_files = os.listdir(CONVERSATIONS_DIRECTORY)
    conversation_names = [
        file_name[:-5]
        for file_name in conversation_files
        if file_name.endswith(".json")
    ]
    return conversation_names


def main():
    user_config = load_user_config()
    parser = argparse.ArgumentParser(description="Anthropic CLI")
    subparsers = parser.add_subparsers(dest="command")

    console = Console()

    chat_parser = subparsers.add_parser(
        "chat", help="Send a message to the AI assistant"
    )
    chat_group = chat_parser.add_mutually_exclusive_group(required=True)
    chat_group.add_argument("message", nargs="?", help="The message to send")
    chat_group.add_argument(
        "-l", "--list-personas", action="store_true", help="List all available personas"
    )
    chat_parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=user_config["model"],
        help="The AI model to use",
    )
    chat_parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=user_config["temperature"],
        help="The temperature value for the AI model",
    )
    chat_parser.add_argument(
        "-p",
        "--persona",
        type=str,
        default=user_config["persona"],
        help="The AI persona to use",
    )
    chat_parser.add_argument(
        "-d",
        "--conversations-directory",
        type=str,
        default=user_config["conversations_directory"],
        help="The directory to store conversation files",
    )
    chat_parser.add_argument(
        "-j", "--json", action="store_true", help="Output the result as JSON"
    )

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
    history_parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Display the conversation history as raw text without formatting",
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
        "conversation_name",
        type=str,
        help="The name of the conversation to import",
    )

    import_parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default=os.path.expanduser("~/conversations"),
        help="The directory containing the conversation file",
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.command == "chat":
        if args.list_personas:
            table = Table(title="Available Personas")
            table.add_column("Persona", style="cyan")
            table.add_column("Description", style="magenta")

            for persona, description in SYSTEM_PROMPTS.items():
                table.add_row(persona, description)

            console = Console()
            console.print(table)
        elif args.remove_last:
            current_conversation_file = get_current_conversation_file()
            if current_conversation_file:
                conversation_history = load_conversation_history(
                    os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file)
                )
                if len(conversation_history) >= 2:
                    conversation_history = conversation_history[:-2]
                    save_conversation_history(
                        conversation_history,
                        os.path.join(
                            CONVERSATIONS_DIRECTORY, current_conversation_file
                        ),
                    )
                    print("Last interaction removed from the conversation history.")
                else:
                    print("No interactions to remove from the conversation history.")
            else:
                print("No conversation history available.")
        else:
            system_message = SYSTEM_PROMPTS.get(args.persona, SYSTEM_PROMPTS["default"])
            role, response = invoke_conversation(
                args.message,
                args.model,
                args.temperature,
                system_message,
                args.conversations_directory,
            )
            if role == "assistant":
                format_assistant_message(response)
            else:
                format_user_message(response)

    elif args.command == "reset":
        reset_conversation()

    elif args.command == "import":
        conversation_name = args.conversation_name
        conversation_directory = args.directory
        conversation_file = f"{conversation_name}.json"
        conversation_path = os.path.join(conversation_directory, conversation_file)

        if os.path.exists(conversation_path):
            set_current_conversation_file(conversation_file)
            console.print(f"Imported conversation: {conversation_name}")
        else:
            console.print(f"Conversation file not found: {conversation_path}")

    elif args.command == "history":
        console.print("Conversation history:")
        current_conversation_file = get_current_conversation_file()
        if current_conversation_file:
            conversation_history = load_conversation_history(
                os.path.join(CONVERSATIONS_DIRECTORY, current_conversation_file)
            )
            for message in conversation_history:
                role = message["role"]
                content = message["content"]
                if not args.raw:
                    if role == "assistant":
                        format_assistant_message(content)
                    else:
                        format_user_message(content)
                else:
                    print(f"{role}: {content}")
        else:
            console.print("No conversation history available.")

    elif args.command == "remove_last":
        current_conversation_file = get_current_conversation_file()
        if current_conversation_file:
            conversation_history = load_conversation_history(
                os.path.join(args.conversations_directory, current_conversation_file)
            )
            if len(conversation_history) >= 2:
                conversation_history = conversation_history[:-2]
                save_conversation_history(
                    conversation_history,
                    os.path.join(
                        args.conversations_directory, current_conversation_file
                    ),
                )
                console.print("Last interaction removed from the conversation history.")
            else:
                console.print(
                    "No interactions to remove from the conversation history."
                )
        else:
            console.print(
                "No active conversation. Start a new conversation with the 'chat' command."
            )


if __name__ == "__main__":
    main()
