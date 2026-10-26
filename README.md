# Fountain Skills

Skills for podcast growth.

Every skill relies on the Fountain API—create an account at [fountain.fm](https://fountain.fm).

Fountain does the daily clip work on its servers, so you need no agent for it.
With Daily Growth on, Fountain finds news trends each day, makes draft clip posts, and renders their videos.
The skills let your agent set up Fountain, find clips when you ask, and build reports.
Two of them do the server work on your machine instead, only when you ask.

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
| `fountain-clip-producer` | Render a clip on your machine instead of on Fountain.                    |
| `fountain-daily-growth`  | Run Daily Growth on your agent instead of on Fountain.                   |
| `fountain-reports`       | Create email reports detailing clip performance and new clip candidates. |

## Data and privacy

The skills send data to the Fountain API, through the Fountain MCP server or through HTTP with a Fountain API key.
How Fountain uses and keeps this data is in the [Fountain privacy policy](https://fountain.fm/privacy-policy).

Some steps send requests to other services:

- The storage URLs that the Fountain Uploads API gives: the clip videos that you render on your machine.
- `media.fountain.fm`: one download of the fonts, the face detection model, and the overlay placeholders that
  skill **fountain-clip-producer** reads, with their licences.
- Google News RSS: the subjects of the show, as search queries (skill **fountain-daily-growth**).
- The web search and social trend tools of the agent, if it has them: search queries about the show and the news.
- The pages that the show publishes outside Fountain, such as its site and its social profiles: page requests.
- YouTube or another video site, through yt-dlp: requests for the video and the captions of a clip source.
- The host of each episode: requests for the episode media.
- Hugging Face: one download of the whisper.cpp model file `ggml-base.en.bin`, for a local render.
- Package managers, such as Homebrew: installs of the software that skill **fountain-onboarding** finds missing.

No skill sends a Fountain API key or a Fountain token to a different service.

The plugin holds no binary files.
Skill **fountain-clip-producer** checks the sha256 of each file that it downloads from `media.fountain.fm`.
ffmpeg and OpenCV read these files as data, and no part of the plugin runs them as code.

## License

[MIT](LICENSE)
