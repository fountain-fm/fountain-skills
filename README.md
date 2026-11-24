# Fountain Skills

Agent skills for podcast growth.

Each morning, Fountain reads the headlines and finds the matching moments in your back catalog.
It turns them into captioned clips in your style, and drafts a post for each of your channels.
You approve the ones you like, and they go out to X, YouTube, Instagram and Facebook.

This plugin connects your agent to Fountain and helps you set it all up: your show, your channels, and the look of
your clips.
After that, just ask your agent, e.g. "Make three clips from my latest episode".
Your agent finds the moments and drafts the posts, and Fountain renders the videos automatically.

You need a [Fountain](https://fountain.fm) account.

## Install

### Claude and Claude Code

1. Open the [Fountain plugin](https://claude.ai/new#customize/plugins/id/0c080483-a976-4807-b9b3-d8ba36b7e03f%40anthropic-plugin-directory)
   and click Add.
   If the link doesn't work, go to Settings → Plugins → Discover and search for Fountain.
2. In the plugin's Connectors tab, click Connect next to Fountain and sign in to your Fountain account.
3. Start a chat and say "Set up Fountain".

On Team and Enterprise plans, your admin may need to allow the plugin.

### ChatGPT and Codex

1. Open the [Fountain plugin](https://chatgpt.com/plugins/plugin_asdk_app_6aa429bc4d1c819198ad6571766be52b)
   and click Install plugin.
2. Sign in to your Fountain account.
3. Start a chat and say "Set up Fountain".

Works in ChatGPT on web, desktop and mobile, and in Codex.

### OpenCode

```sh
# Add the Fountain MCP server
opencode mcp add fountain --url https://api.fountain.fm/v1/mcp --global
# Sign in to your Fountain account in the browser
opencode mcp auth fountain
# Install the Fountain skills
npx skills add fountain-fm/fountain-skills -g -a opencode -s '*' -y
```

Start OpenCode and say "Set up Fountain".

### Hermes

```sh
# Add the Fountain MCP server, sign in to your Fountain account in the browser, and enable all tools
hermes mcp add fountain --url https://api.fountain.fm/v1/mcp --auth oauth --connect-timeout 300
# Install the Fountain skills
npx skills add fountain-fm/fountain-skills -g -a hermes-agent -s '*' -y
```

Start Hermes and say "Set up Fountain".

### OpenClaw

```sh
# Add the Fountain MCP server
openclaw mcp set fountain '{"url":"https://api.fountain.fm/v1/mcp","transport":"streamable-http","auth":"oauth"}'
# Sign in to your Fountain account in the browser
openclaw mcp login fountain
# Install the Fountain skills
npx skills add fountain-fm/fountain-skills -g -a openclaw -s '*' -y
```

Restart OpenClaw and say "Set up Fountain".

### Any other agent

1. Add an MCP server named Fountain with the URL `https://api.fountain.fm/v1/mcp`.
   Leave the OAuth client ID and secret empty.
2. Sign in to your Fountain account when your agent asks.
3. Install the Fountain skills.
   The CLI asks which agent to install for.

   ```sh
   npx skills add fountain-fm/fountain-skills -g
   ```

4. Start your agent and say "Set up Fountain".

## The skills

| Skill                 | What it does                                                                           |
| --------------------- | -------------------------------------------------------------------------------------- |
| `fountain-onboarding` | Sets up your show, your channels, and the look of your clips, then makes a first clip. |

## What the Fountain tools can do

The Fountain MCP server gives tools that read your Fountain data, and tools that change it.
The tools that change it can:

- Publish a social post now or at a set time on a connected channel, and delete a post that is not published.
- Connect a social channel, after you approve access on that platform.
- Publish, schedule, change or delete an episode in a podcast feed that Fountain hosts.
- Change the settings and the preferences of a project.
- Spend project credits, e.g. when Fountain makes a clip draft or a transcript.

The skills publish nothing until you approve it.

## Data and privacy

The skills send data to the Fountain API through the Fountain MCP server.
How Fountain uses and keeps this data is in the [Fountain privacy policy](https://fountain.fm/privacy-policy).

Some steps send requests to other services:

- The web search tools of the agent, if it has them: search queries about the show.
- The pages that the show publishes outside Fountain, such as its site and its social profiles: page requests.

No skill sends a Fountain token to a different service.

The plugin holds no binary files.

## Package an OpenAI update

Commit your changes, then run:

```sh
npm run package:openai
```

Upload `dist/fountain-openai-<version>.zip` to the existing Fountain plugin in the OpenAI developer dashboard.

## License

[MIT](LICENSE)
