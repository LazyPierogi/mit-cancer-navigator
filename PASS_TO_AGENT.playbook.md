# Pass To Agent

Use this file as the final handoff prompt for your coding agent after bootstrap.

## What was installed
- AGENTS file: /Users/mario/repo/mit-cancer-navigator/AGENTS.md
- Project memory file: /Users/mario/repo/mit-cancer-navigator/PROJECT_MEMORY.md
- Startup checklist file: /Users/mario/repo/mit-cancer-navigator/STARTUP_CHECKLIST.md
- Setup review file: /Users/mario/repo/mit-cancer-navigator/SETUP_PROJECT_FIT_REVIEW.playbook.md
- Repo MCP source-of-truth file: /Users/mario/repo/mit-cancer-navigator/mcp.json
- MCP update script: /Users/mario/repo/mit-cancer-navigator/scripts/update_windsurf_mcp.py
- Playbook workspace: /Users/mario/repo/mit-cancer-navigator/.ai-playbook
- Selected packs: none
- MCP mode(s): skip
- Skill install mode: yes
- Project skills directory: /Users/mario/repo/mit-cancer-navigator/.codex/skills
- Selected skills: ai-agents-architect api-security-best-practices api-security-testing appdeploy application-performance-performance-optimization architect-review architecture
- Installed skills: ai-agents-architect api-security-best-practices api-security-testing appdeploy application-performance-performance-optimization architect-review architecture

## Expected outputs (MCP)
Use this checklist to validate MCP artifacts were generated as expected for the selected MCP mode(s).

- [ ] MCP mode includes 'skip': no MCP files are required.

## Agent mission
1. Read AGENTS.md, PROJECT_MEMORY.md, STARTUP_CHECKLIST.md, .ai-playbook/INSTALLATION_SUMMARY.md, and SETUP_PROJECT_FIT_REVIEW.playbook.md.
2. Read the project description (provided by the user) and execute the setup review checklist to validate Skills + MCP setup against actual project needs.
   - Input: a file path in this repo OR pasted description text.
   - Goal: confirm selected packs, installed skills, and MCP servers are appropriate; detect missing items early.
3. Determine repository state:
   - If this is a clean repo: initialize missing baseline docs and start the checklist.
   - If this is an existing repo: merge playbook rules with current docs without deleting existing project context.
4. Apply pack add-ons from .ai-playbook/templates/packs/ only when relevant to this project.
5. Keep MCP source-of-truth in repo:
   - update /Users/mario/repo/mit-cancer-navigator/mcp.json with concrete MCP server config entries required by this project.
6. Never edit /Users/mario/.codeium/windsurf/mcp_config.json directly from repo automation.
   - instead, run: python3 /Users/mario/repo/mit-cancer-navigator/scripts/update_windsurf_mcp.py
   - then click Refresh in Windsurf MCP settings.
7. Skills + MCP validation steps (do this before claiming bootstrap is complete):
   - Re-evaluate whether the currently selected packs match the project description.
   - Compare required capabilities to the installed skills list in .ai-playbook/INSTALLATION_SUMMARY.md.
   - Treat skills as project-local assets stored in /Users/mario/repo/mit-cancer-navigator/.codex/skills, not global IDE assets.
   - If a skill is missing and you can install skills in your environment safely, install it into /Users/mario/repo/mit-cancer-navigator/.codex/skills.
   - If you cannot install automatically, output a concrete install plan (commands/steps) for the user.
   - Validate MCP setup:
     - Ensure the generated MCP files exist in the repo (if selected during bootstrap).
     - Ensure the active MCP client configuration includes the required servers for this project.
     - If you can update the MCP config safely, do so; otherwise provide exact manual steps.
8. Produce a short execution report with:
   - What was merged
   - What was skipped and why
   - Skills/MCP validation results (missing, installed, or deferred with instructions)
   - Open decisions requiring human input
9. Update SETUP_PROJECT_FIT_REVIEW.playbook.md decision table and completion gate checkboxes.

## Project description input (required)
Provide ONE of the following to the agent:
- A file path in this repository that contains a project description / pitch / requirements.
- Or paste the project description text directly into the prompt.

If the project description is missing or ambiguous, the agent must ask for clarification before changing packs/skills/MCP.

## Ready-to-copy prompt
```text
You are continuing a playbook bootstrap in this repository.
Read PASS_TO_AGENT.playbook.md and execute the Agent mission exactly.

Project description file path (preferred): <PASTE_PATH_HERE>
If no file path is available, paste the project description here instead:
<PASTE_PROJECT_DESCRIPTION_TEXT_HERE>

Validate that the installed Skills and MCP servers match this project's needs.
Use project-local skills from /Users/mario/repo/mit-cancer-navigator/.codex/skills rather than installing into global IDE skill storage.
Update mcp.json in repo as source-of-truth, then run scripts/update_windsurf_mcp.py to apply global Windsurf MCP changes.
If anything is missing, install it in your environment when possible; otherwise provide concrete install instructions.
Work in small, verifiable steps and produce the execution report at the end.
```
