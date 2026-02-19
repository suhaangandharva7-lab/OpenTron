# Agents: Operational Baseline & Security

- **Core Rule**: "Trust but Verify."
- **Unlimited Hands Protocol**: 
  - Every GUI action (click, type) requires explicit approval.
  - Every global file system operation (outside workspace) requires a **HIGH RISK** approval prompt.
- **Security**: Never execute destructive commands without explicit user approval.
- **Sandboxing**: By default, use `./workspace`. Global access is granted on a per-command basis via specialized tools.
- **Privacy**: Screenshots must be shared with the user in the Telegram chat to maintain transparency.
