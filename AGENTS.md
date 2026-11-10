# For AI coding agents (Claude Code, Codex, Gemini CLI, Cursor…)

To install this project for a user, follow `skill/effacement-donnees/SKILL.md` step by step (it is written in French; ask the user one question at a time). The core program needs no AI: `installer.py` and `effacement/agent.py` are plain Python.

Rules that always apply:
- Never put personal data in the repository: everything personal goes to `donnees/` through `installer.py` (git-ignored).
- Never send anything during setup: use `python3 installer.py essai` (dry run).
- The weekly research agent runs any tool set in `RECHERCHE_CMD` (default: Claude Code with web search, read access to its folder and write access to its single proposals file, no shell). Give another tool the same limits.
