from datetime import datetime
import markdown
from rich.console import Console
from rich.style import Style
from rich.syntax import Syntax

# from rich.table import Table
from rich.progress import Progress
from rich.markdown import Markdown
# from rich.panel import Panel

console = Console()

title_style = Style(
    color="green",
    bold=True,
)
user_style = Style(color="magenta")
assistant_style = Style(color="#7dcfff")

user_avatar = "😊"
assistant_avatar = "🤖"


def format_user_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # user_text = Align(
    #     Text(f"{user_avatar} {message}\n", style=user_style),
    #     # + Text(timestamp, style="dim"),
    #     align="right",
    # )
    console.print(Markdown(message, style=user_style, code_theme="ansi_dark"))


def format_assistant_message(message):
    lines = message.split("\n")
    in_code_block = False
    code_block_lines = []

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                # End of code block
                code_block = "\n".join(code_block_lines)
                syntax = Syntax(code_block, "python", line_numbers=False)
                console.print(syntax)
                code_block_lines = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
                language = line[
                    3:
                ].strip()  # Extract the language from the code block delimiter
                if not language:
                    language = (
                        "python"  # Default to 'python' if no language is specified
                    )
        else:
            if in_code_block:
                code_block_lines.append(line)
            else:
                console.print(line, style=assistant_style, highlight=False)


def format_conversation_title(title):
    console.print(f"Title: {title}", style=title_style)


def format_code_block(code, language):
    syntax = Syntax(code, language, line_numbers=True)
    console.print(syntax)


# def format_table(data, header):
#     table = Table(header=header)
#     for row in data:
#         table.add_row(*row)
#     console.print(table)


def format_progress(total, current, description):
    with Progress() as progress:
        task = progress.add_task(description, total=total)
        progress.update(task, completed=current)


def format_markdown(markdown):
    md = Markdown(markdown)
    console.print(md)


def format_image(image_path):
    with open(image_path, "r") as image_file:
        image = image_file.read()
    console.print(image)
