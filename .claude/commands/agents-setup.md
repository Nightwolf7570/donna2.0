---
description: Creates agents for your tech stack
argument-hint: [PRD.json or doc describing what agent is in charge of]
---

# Command: Agents Setup

If not already existing, create agents in the folder `.claude/agents/` for each tool in the tech stack describes in the mentioned document.

Notes:
- Agents are created with kebab-case naming: `agent-feature-name.md`
- Agents should be specific to technologies used like APIs or frameworks rather than features.
- Use skill `agent-creating` to create agents
- Always use context7 for the latest information, documentation, and best practices. If context7 MCP is not available. STOP and ask the user to install it. Do not proceed without using the MCP.