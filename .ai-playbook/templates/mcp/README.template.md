# MCP Templates

This folder provides minimal MCP starter templates for:
- Universal servers (cross-project baseline)
- Specific server for game development (Unity)
- Specific server for Apple-native/mobile projects (Xcode Tools via `xcrun mcpbridge`)
- Recommendation template for non-game project types

Use these files as merge sources for your active MCP client configuration.

## Windsurf update model
- Keep runnable MCP entries in repository root `mcp.json` as source-of-truth.
- Apply changes to global Windsurf MCP config with:
  - `python3 scripts/update_windsurf_mcp.py`
- After running the script, click `Refresh` in Windsurf MCP settings.
- Do not edit `~/.codeium/windsurf/mcp_config.json` directly from agent workflows.

## Recommended universal pairing for GitHub-heavy work
- Add `deepwiki-mcp` to universal MCP for faster repository comprehension.
- Use `deepwiki-mcp` with GitHub MCP or GitHub CLI when porting/reimplementing functionality from existing repositories.

Example prompt:
```text
Use DeepWiki MCP and Github CLI to look at how torchao implements fp8 training. Is it possible to 'rip out' the functionality? Implement nanochat/fp8.py that has identical API but is fully self-contained
```
