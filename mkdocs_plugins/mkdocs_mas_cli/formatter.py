"""Markdown formatting utilities for argparse documentation."""

import argparse
from typing import Dict


class MarkdownFormatter:
    """Format ArgumentParser as markdown documentation."""

    def format_parser(self, parser: argparse.ArgumentParser, ignore_description: bool = False, ignore_epilog: bool = False) -> str:
        """Generate complete markdown documentation from ArgumentParser.

        Args:
            parser: ArgumentParser instance to format
            ignore_description: If True, skip the description section
            ignore_epilog: If True, skip the epilog section

        Returns:
            Formatted markdown documentation
        """
        sections = []

        # Usage section
        usage = self.format_usage(parser)
        if usage:
            sections.append(usage)

        # Description section
        if not ignore_description:
            description = self.format_description(parser)
            if description:
                sections.append(description)

        # Argument groups - now with consistent column widths
        groups = self.format_argument_groups(parser)
        if groups:
            sections.append(groups)

        # Epilog section
        if not ignore_epilog:
            epilog = self.format_epilog(parser)
            if epilog:
                sections.append(epilog)

        return '\n\n'.join(sections)

    def format_usage(self, parser: argparse.ArgumentParser) -> str:
        """Generate usage synopsis."""
        prog = parser.prog or "command"
        return f"""## Usage

```bash
{prog} [OPTIONS]
```"""

    def format_description(self, parser: argparse.ArgumentParser) -> str:
        """Generate description section."""
        if not parser.description:
            return ""

        # Clean up description (may have multiple lines)
        desc_lines = parser.description.strip().split('\n')
        description = '\n'.join(line.strip() for line in desc_lines)

        return f"""### Description

{description}"""

    def format_epilog(self, parser: argparse.ArgumentParser) -> str:
        """Generate epilog section."""
        if not parser.epilog:
            return ""

        return f"""### Additional Information

{parser.epilog.strip()}"""

    def format_argument_groups(self, parser: argparse.ArgumentParser) -> str:
        """Generate HTML tables for all argument groups with consistent column widths."""
        # Collect all groups and their data
        groups_data = []

        for group in parser._action_groups:
            # Skip default groups with no custom title
            if group.title in ('positional arguments', 'optional arguments', 'options'):
                actions = [a for a in group._group_actions if a.dest != 'help']
                if not actions:
                    continue
            else:
                actions = [a for a in group._group_actions if a.dest != 'help']

            if not actions:
                continue

            # Collect data for this group
            group_info = {
                'title': group.title or "Options",
                'description': group.description,
                'rows': []
            }

            for action in actions:
                row_data = self._get_argument_data(action)
                group_info['rows'].append(row_data)

            groups_data.append(group_info)

        # Format all groups as HTML tables with fixed column widths
        sections = []
        for group_info in groups_data:
            section = self._format_group_as_html(group_info)
            sections.append(section)

        return '\n\n'.join(sections)

    def _get_argument_data(self, action) -> Dict[str, str]:
        """Extract argument data as a dictionary."""
        # Option flags (without backticks for HTML)
        option_strings = ', '.join(f"<code>{opt}</code>" for opt in action.option_strings)
        if not option_strings:
            option_strings = f"<code>{action.dest}</code>"

        # Type/Choices (format for HTML)
        type_str = self.format_type_html(action)

        # Default value (format for HTML)
        default_str = self.format_default_html(action)

        # Description (escape for HTML)
        help_text = self.escape_html(action.help or "")

        return {
            'option': option_strings,
            'type': type_str,
            'default': default_str,
            'description': help_text
        }

    def _format_group_as_html(self, group_info: Dict) -> str:
        """Format a group as an HTML table with fixed column widths."""
        lines = [f"### {group_info['title']}"]

        # Add group description if present
        if group_info['description']:
            lines.append("")
            lines.append(group_info['description'])

        # HTML table with fixed column widths
        lines.append("")
        lines.append('<table style="width: 100%; table-layout: fixed;">')
        lines.append('  <colgroup>')
        lines.append('    <col style="width: 25%;">')  # Option column
        lines.append('    <col style="width: 15%;">')  # Type column
        lines.append('    <col style="width: 15%;">')  # Default column
        lines.append('    <col style="width: 45%;">')  # Description column
        lines.append('  </colgroup>')
        lines.append('  <thead>')
        lines.append('    <tr>')
        lines.append('      <th>Option</th>')
        lines.append('      <th>Type</th>')
        lines.append('      <th>Default</th>')
        lines.append('      <th>Description</th>')
        lines.append('    </tr>')
        lines.append('  </thead>')
        lines.append('  <tbody>')

        # Table rows
        for row_data in group_info['rows']:
            lines.append('    <tr>')
            lines.append(f'      <td>{row_data["option"]}</td>')
            lines.append(f'      <td>{row_data["type"]}</td>')
            lines.append(f'      <td>{row_data["default"]}</td>')
            lines.append(f'      <td>{row_data["description"]}</td>')
            lines.append('    </tr>')

        lines.append('  </tbody>')
        lines.append('</table>')

        return '\n'.join(lines)

    def format_type(self, action) -> str:
        """Format the type/choices for an argument (markdown version)."""
        if action.choices:
            choices = ', '.join(str(c) for c in action.choices)
            return f"`{{{choices}}}`"
        elif isinstance(action, argparse._StoreTrueAction):
            return "flag"
        elif isinstance(action, argparse._StoreFalseAction):
            return "flag"
        elif isinstance(action, argparse._StoreConstAction):
            return "flag"
        elif action.type:
            return f"`{action.type.__name__}`"
        else:
            return "`string`"

    def format_type_html(self, action) -> str:
        """Format the type/choices for an argument (HTML version)."""
        if action.choices:
            choices = ', '.join(str(c) for c in action.choices)
            return f"<code>{{{choices}}}</code>"
        elif isinstance(action, argparse._StoreTrueAction):
            return "flag"
        elif isinstance(action, argparse._StoreFalseAction):
            return "flag"
        elif isinstance(action, argparse._StoreConstAction):
            return "flag"
        elif action.type:
            return f"<code>{action.type.__name__}</code>"
        else:
            return "<code>string</code>"

    def format_default(self, action) -> str:
        """Format the default value for an argument (markdown version)."""
        if action.default is None or action.default == argparse.SUPPRESS:
            return "-"
        elif isinstance(action.default, bool):
            return f"`{str(action.default).lower()}`"
        elif isinstance(action.default, str):
            if action.default == "":
                return '`""`'
            return f"`{action.default}`"
        else:
            return f"`{action.default}`"

    def format_default_html(self, action) -> str:
        """Format the default value for an argument (HTML version)."""
        if action.default is None or action.default == argparse.SUPPRESS:
            return "-"
        elif isinstance(action.default, bool):
            return f"<code>{str(action.default).lower()}</code>"
        elif isinstance(action.default, str):
            if action.default == "":
                return '<code>""</code>'
            return f"<code>{self.escape_html(action.default)}</code>"
        else:
            return f"<code>{action.default}</code>"

    def escape_markdown(self, text: str) -> str:
        """Escape special markdown characters in text."""
        if not text:
            return ""

        # Escape pipe characters in table cells
        text = text.replace('|', '\\|')

        # Handle backticks - don't escape if already in code
        # This is a simple heuristic
        if '`' in text and not text.count('`') % 2 == 0:
            text = text.replace('`', '\\`')

        return text

    def escape_html(self, text: str) -> str:
        """Escape special HTML characters in text."""
        if not text:
            return ""

        # Escape HTML special characters (ampersand first!)
        text = text.replace('&', '\x26amp;')
        text = text.replace('<', '\x26lt;')
        text = text.replace('>', '\x26gt;')
        text = text.replace('"', '\x26quot;')
        text = text.replace("'", '\x26#39;')

        return text


# Made with Bob
