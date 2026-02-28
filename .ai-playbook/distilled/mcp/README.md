# MCP Catalog

## Universal MCP Baseline
- `github-mcp-server`: [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)
- `CodeGraphContext`: [github.com/CodeGraphContext/CodeGraphContext](https://github.com/CodeGraphContext/CodeGraphContext)
- `context7`: [github.com/upstash/context7](https://github.com/upstash/context7)
- `deepwiki-mcp`: [docs.devin.ai/work-with-devin/deepwiki-mcp](https://docs.devin.ai/work-with-devin/deepwiki-mcp)
- `firecrawl`: [github.com/mendableai/firecrawl](https://github.com/mendableai/firecrawl)
- `playwright-mcp`: [github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)

## Specific MCP
- Game development:
  - `unity-mcp`: [github.com/CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp)
- Apple-native/mobile development:
  - `xcode` via `xcrun mcpbridge` (Xcode Tools MCP bridge)
  - In Xcode: Settings -> Intelligence -> Model Context Protocol -> enable Xcode Tools.
  - CLI examples:
    - `claude mcp add --transport stdio xcode -- xcrun mcpbridge`
    - `codex mcp add xcode -- xcrun mcpbridge`
  - Verify:
    - `claude mcp list` or `codex mcp list`

## Recommendation Rule (without built-in specific template)
- Start with Universal baseline.
- Ask the agent to recommend one specific MCP server based on project constraints.
- Use this catalog as the source list for recommendations:
  - [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
- Add more only if there is a measurable need (capability gap, speed, or reliability).

## Agent Usage Pattern (DeepWiki + GitHub)
- Use `deepwiki-mcp` to understand unfamiliar repositories quickly before extraction/refactor.
- Pair `deepwiki-mcp` with GitHub MCP or GitHub CLI for code-level verification and implementation.
- Prefer this flow:
  1. Map architecture and target implementation in DeepWiki.
  2. Locate exact files and symbols via GitHub tooling.
  3. Re-implement as self-contained code with identical external API.

Example prompt:
```text
Use DeepWiki MCP and Github CLI to look at how torchao implements fp8 training. Is it possible to 'rip out' the functionality? Implement nanochat/fp8.py that has identical API but is fully self-contained
```
