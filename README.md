# Fountain

Agent skills for podcast growth.

Each morning, Fountain reads the headlines and finds the matching moments in your back catalog.
It turns them into captioned clips in your style, and drafts a post for each of your channels.
You approve the ones you like, and they go out to X, YouTube and Instagram.

This plugin connects Claude to Fountain and helps you set it all up: your show, your channels, and the look of
your clips.
After that, just ask Claude, e.g. "Make three clips from my latest episode".
Claude finds the moments and drafts the posts, and Fountain renders the videos automatically.

You need a [Fountain](https://fountain.fm) account.

## Install

1. Open the [Fountain plugin](https://claude.ai/new#customize/plugins/id/0c080483-a976-4807-b9b3-d8ba36b7e03f%40anthropic-plugin-directory)
   and click Add.
   If the link doesn't work, go to Settings → Plugins → Discover and search for Fountain.
2. In the plugin's Connectors tab, click Connect next to Fountain and sign in to your Fountain account.
3. Start a chat and say "Set up Fountain".

For the best experience, we recommend Claude Code.
On Team and Enterprise plans, your admin may need to allow the plugin.

## The skills

| Skill                 | What it does                                                                |
| --------------------- | --------------------------------------------------------------------------- |
| `fountain-onboarding` | Sets up your show, your channels, the look of your clips, and Daily Growth. |

## Data and privacy

The skills send data to the Fountain API through the Fountain MCP server.
How Fountain uses and keeps this data is in the [Fountain privacy policy](https://fountain.fm/privacy-policy).

Some steps send requests to other services:

- The web search tools of the agent, if it has them: search queries about the show.
- The pages that the show publishes outside Fountain, such as its site and its social profiles: page requests.

No skill sends a Fountain token to a different service.
The plugin installs no software and holds no binary files.

## License

[MIT](LICENSE)
