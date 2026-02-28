# MCP Specific Recommendation

No fixed specific MCP server was auto-selected for this project type.

Use an agent-assisted recommendation based on the MCP catalog in:
- `.ai-playbook/distilled/mcp/README.md`
- `https://github.com/punkpeye/awesome-mcp-servers`

Recommendation policy:
- Keep Universal MCP as your baseline.
- Add Specific MCP only when a project constraint clearly requires it.
- Prefer one specific server at first, then expand only if needed.

Apple-native note:
- If your project is iOS/macOS/Xcode-first, prefer Xcode Tools MCP bridge:
  - In Xcode: Settings -> Intelligence -> Model Context Protocol -> enable Xcode Tools.
  - Claude Code setup:
    - `claude mcp add --transport stdio xcode -- xcrun mcpbridge`
  - Codex setup:
    - `codex mcp add xcode -- xcrun mcpbridge`
  - Verify:
    - `claude mcp list` or `codex mcp list`
