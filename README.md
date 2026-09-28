# Fountain Skills

Skills for podcast growth.

Every skill relies on the Fountain API—create an account at [fountain.fm](https://fountain.fm).

## Install

### Codex

Codex plugin bundles Fountain skills and MCP.

Sign in to Fountain when Codex asks you to authenticate the MCP connection.

In chat (preferably Codex), say "Set up Fountain".

### Claude

Claude plugin bundles Fountain skills and MCP.

1. On [claude.ai](https://claude.ai), open **Settings** in the sidebar
2. Go to **Plugins**
3. Press Add > Add marketplace > Add from a repository
4. Paste in `https://github.com/fountain-fm/fountain-skills` and press Sync
5. In chat (preferably Claude Code), say "Set up Fountain"

### Claude Code

Run these commands in Claude Code:

```
/plugin marketplace add fountain-fm/fountain-skills
/plugin install fountain@fountain-skills
```

Then say "Set up Fountain".

## The skills

| Skill                    | Job                                                                      |
| ------------------------ | ------------------------------------------------------------------------ |
| `fountain-onboarding`    | Set up Fountain.                                                         |
| `fountain-clip-finder`   | Search the transcripts, find clippable moments, and create draft posts.  |
| `fountain-clip-producer` | Produce videos for candidate clips with framing, captions, and overlays. |
| `fountain-daily-growth`  | Read yesterday's numbers and today's news, then brief the clip finder.   |
| `fountain-reports`       | Create email reports detailing clip performance and new clip candidates. |

## Data and privacy

The skills send data to the Fountain API, through the Fountain MCP server or through HTTP with a Fountain API key.
The [Fountain privacy policy](https://fountain.fm/privacy-policy) tells how Fountain uses and keeps this data.

Some steps send requests to other services:

- The storage URLs that the Fountain Uploads API gives: the rendered clip videos.
- Google News RSS: the subjects of the show, as search queries (skill **fountain-daily-growth**).
- The web search and social trend tools of the agent, if it has them: search queries about the show and the news.
- YouTube, through yt-dlp: requests for the video and the captions of a clip source.
- The host of each episode: requests for the episode media.
- Hugging Face: one download of the whisper.cpp model file.
- Package managers, such as Homebrew: installs of the software that skill **fountain-onboarding** finds missing.

The skills do not send a Fountain API key or a Fountain token to a different service.
Rendering, framing, and captions occur on the machine that runs the agent.

The fonts and the ONNX face detection model in skill **fountain-clip-producer** are data files.
ffmpeg and OpenCV read them, and no part of the plugin runs them as code.

## License

[MIT](LICENSE)
