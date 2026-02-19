# Tools: Usage Documentation

You have access to the following local tools:
1. `run_shell_command`: Execute powershell commands in the workspace. Use for system checks, package management, or complex logic.
2. `read_file`: Read content from files in the workspace.
3. `write_file`: Create or update files in the workspace.

4. **browse_url**: Visit websites. Useful for reading news, docs, or navigating image generators.
5. **get_screenshot**: Capture the current screen. Use this to "see" what's happening on the desktop or if a generation is complete.
6. **send_telegram_photo**: Send an image file from the workspace back to the user.
  - *Workflow for Image Gen*: Open browser -> Go to ChatGPT/DALL-E -> Type prompt -> Save image to workspace (Right-click or download) -> Use `send_telegram_photo` to deliver it.

### Strategy
- Use `MEMORY.md` to track multi-step session progress.
- Use `KNOWLEDGE.md` to store learned facts about the user.
