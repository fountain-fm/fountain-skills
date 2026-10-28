# Fountain Skills

Clips worth posting, every morning.

Each morning, Fountain reads the headlines and finds the moments in your back catalog that match.
It turns them into captioned clips in your style, and writes a post for each of your channels.
You approve the ones you like, and they go out to X, YouTube and Instagram.

This plugin connects your agent to Fountain and helps you set it all up: your show, your channels, and the look of
your clips.
After that, just ask your agent, e.g. "Make the captions bigger on my latest clip".

You need a [Fountain](https://fountain.fm) account.

## Install

### Claude and Claude Code

1. Open the [Fountain plugin](https://claude.ai/new#customize/plugins/id/0c080483-a976-4807-b9b3-d8ba36b7e03f%40anthropic-plugin-directory)
   and click Add.
   If the link doesn't work, go to Settings → Plugins → Discover and search for Fountain.
2. In the plugin's Connectors tab, click Connect next to Fountain and sign in to your Fountain account.
3. Start a chat and say "Set up Fountain".

For the best experience, we recommend Claude Code.
On Team and Enterprise plans, your admin may need to allow the plugin.

### ChatGPT and Codex

1. Open the [Fountain plugin](https://chatgpt.com/plugins/plugin_asdk_app_6aa429bc4d1c819198ad6571766be52b)
   and click Install plugin.
2. Sign in to your Fountain account.
3. Start a chat and say "Set up Fountain".

Works in ChatGPT on web, desktop and mobile, and in Codex.
For the best experience, we recommend Codex.

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

| Skill                    | What it does                                                                |
| ------------------------ | --------------------------------------------------------------------------- |
| `fountain-onboarding`    | Sets up your show, your channels, the look of your clips, and Daily Growth. |
| `fountain-clip-producer` | Renders a clip on your own computer, when you ask for it.                   |

## Data and privacy

The skills send data to the Fountain API, through the Fountain MCP server or through HTTP with a Fountain API key.
How Fountain uses and keeps this data is in the [Fountain privacy policy](https://fountain.fm/privacy-policy).

Some steps send requests to other services:

- The storage URLs that the Fountain Uploads API gives: the clip videos that you render on your machine.
- `media.fountain.fm`: one download of the fonts, the face detection model, and the overlay placeholders that
  skill **fountain-clip-producer** reads, with their licences.
- The web search tools of the agent, if it has them: search queries about the show.
- The pages that the show publishes outside Fountain, such as its site and its social profiles: page requests.
- YouTube or another video site, through yt-dlp: requests for the video and the captions of a local render.
- The host of each episode: requests for the episode media of a local render.
- Hugging Face: one download of the whisper.cpp model file `ggml-base.en.bin`, for a local render.
- Package managers, such as Homebrew: installs of the software that a local render needs, when you agree.

No skill sends a Fountain API key or a Fountain token to a different service.

The plugin holds no binary files.
Skill **fountain-clip-producer** checks the sha256 of each file that it downloads from `media.fountain.fm`.
ffmpeg and OpenCV read these files as data, and no part of the plugin runs them as code.

## License

[MIT](LICENSE)
