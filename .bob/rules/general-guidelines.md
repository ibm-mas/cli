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
5. **Always ask for clarification** if you are unsure about the requirements or context
    - Do not pose leading questions


## Windows Development with WSL
Inspect the system information in `environment_details.md` for the operating system, if `Operating System: Windows` and `Default Shell: powershell` wrap **all** commands with WSL exactly as follows: `wsl bash -lc "{COMMAND}"`


## Planning
Use the **new_task** tool with mode set to "plan" to generate a plan before making non-trivial changes, **even if not explicitly asked to create a plan**.

You MUST immediately use **new_task** to spawn a planning subtask. Do NOT:
- Read files first to "understand the codebase"
- Gather information before starting the plan
- Perform any analysis in the current task

**All research and analysis must happen within the planning subtask.**

The prompt to the subtask must inform that `attempt_completion` must be used once the plan has been created and not to proceed with the implementation.

### Naming
- Use `.bob/plans/` for planning documents
- Name files descriptively using a timestamp, e.g. `2026-04-30-design-review.md`

### Structure
1. **Objective** - Brief summary of what we are trying to achieve (1-2 sentences)

2. **Design Decisions** (optional) - Document key design choices made during planning
   - Schema definitions, data structures, algorithms
   - Rationale for architectural decisions
   - Edge cases and how they're handled
   - **This section IS the design document** - do not create phases to "create design documents"

3. **Critical Rules** - Bullet point list of key rules for agents to obey
   - Use when there are specific constraints or requirements that must not be violated
   - Examples: "Introduce no functional changes", "Preserve all existing tests", "Perform validation after every change"
   - Keep concise and actionable
   - Include a reminder to track progress ONLY in the plan document, NOT in chat todo lists

4. **Execution Plan** - Checklist of implementation actions to be taken
   - **Start with Phase 1 as the first implementation step** - the plan itself is not a phase
   - Break down into phases for complex plans
   - Each phase should have:
     - Clear objective and scope
     - Instructions to use the **new_task** tool to launch a subtask to complete the phase
     - Numbered checkboxes for all actions (e.g., `[ ] **1.1** Create file X`)
     - Sub-checkboxes for detailed steps within actions
     - Validation step at end of phase before completing the subtask
   - When ordering actions, prioritize easy wins and small tasks before complex tasks

5. **Final Validation** - Details on how to perform validation
   - Specify commands to run
   - Define success criteria
   - Include troubleshooting guidance if applicable

### Requirements
- Plans must be **definitive** and **actionable**
- Do not leave open questions in the plan, prompt the developer to make decisions and provide answers where necessary

### Plan Execution & Tracking
**Critical:** Track progress ONLY in the plan document, NOT in chat todo lists
- Do NOT use `update_todo_list` tool - it creates redundant tracking in chat
- Update the plan markdown file directly using `apply_diff` to mark completed items
- Mark completed items with `[x]` and add completion notes/timestamps if helpful
- **For iterative tasks**: Update checklist after each successful iteration/validation
- **For multi-step phases**: Update after completing each major step within the phase
- **Before using `attempt_completion`**: Ensure plan reflects all completed work
- The plan document is the single source of truth for task progress
