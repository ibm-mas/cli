#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles.named_colors import NAMED_COLORS

print = print_formatted_text


def main():
    tokens = FormattedText([("fg:" + name, name + "  ") for name in NAMED_COLORS])

    print(HTML("\n<u>Named colors, use 256 colors.</u>"))
    print(tokens)


if __name__ == "__main__":
    main()
