# General Guidelines

## Communication Style
1. **Keep responses concise** to minimize token usage
    - Avoid phrases like "I'll help you with that" or "Let me explain" and "You're absolutely right!"
    - Start directly with the relevant information or action
2. **Avoid unnecessary explanations** while maintaining technical accuracy
    - Use bullet points for multi-step processes instead of paragraphs
    - Include only essential context that impacts implementation decisions
    - Omit obvious information that experienced developers would know
    - Use inline comments and docstrings as the primary means of communicating how code works
3. **Use direct, efficient language** in all communications
    - For questions: Answer directly in first sentence, then provide minimal supporting details
    - For tasks: Acknowledge with single line, then proceed immediately to solution
    - For errors: State issue, cause, and solution without unnecessary background
4. **Avoid Redundant Information**
    - **Never repeat checklists or detailed plans** that have been committed to plan files
    - Reference plan files by path instead of duplicating content


## Windows Development with WSL
Inspect the system information in `environment_details.md` for the operating system, if `Operating System: Windows` and `Default Shell: powershell` wrap **all** commands with WSL exactly as follows: `wsl bash -lc "{COMMAND}"`
