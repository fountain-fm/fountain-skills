## Overview

This housekeeping file is the same for every Fountain skill.
It is enough to read it once per session.

The reader does not develop fountain-skills.

## About fountain-skills

Fountain has an MCP that wraps around its API.

Fountain also provides public skills for podcast growth.
Most of them rely on the Fountain API.

github.com/fountain-fm/fountain-skills contains

- all the skills (including this file)
- the configuration files for the MCP and the agent plugins

Plugins are an abstraction that packages together

1. the MCP
2. the skills

The plugin is the preferred way to install Fountain MCP and skills because it receives regular updates.

### API

The API can

- load project information
- load public shows, episodes, and transcripts
- search across public content and transcripts
- publish your podcasts
- publish social posts

It can be reached via one of two routes.

#### Route A: MCP (preferred)

- MCP enables Fountain users to authenticate via OAuth instead of generating API keys
- MCP provides tools for different API groups
- For additional information, you can read the docs at https://beta.fountain.fm/docs.md
- If MCP is not connected, ask the user to connect it via the MCP Server URL

Config:

- Server URL: https://api.fountain.fm/v1/mcp
- Authorization: Fountain User OAuth

#### Route B: HTTP (discouraged)

- MUST read https://beta.fountain.fm/docs.md in each new session
- Find the API key in the `FOUNTAIN_API_KEY` environment variable or in `.env`
- If no key, ask the user to make one at https://beta.fountain.fm/studio/projects
- A Fountain key starts with `fountain_`.
  When a request fails to authenticate under a key with a different prefix, the key is for another
  service, and you MUST tell the user.
- You MUST NOT write the key into a log, a command, a report, or any file but the key store.

Config:

- Base URL: https://api.fountain.fm/v1
- Authorization: Fountain API Key as Bearer Key

#### Additional details

- If you think the MCP/API is not connected / authenticated, double check by trying to list the projects.
  Don't just assume it isn't working.
- Write a large response to a file and read only the part you need.
- You CAN write a throwaway script, e.g. to repeat one request over many items.
  Put it in a temporary place and delete it at the end of the session.
  You MUST NOT keep a script that wraps the API, because the API can change.

## Setup

Skill **fountain-onboarding** ensures Fountain and the user's environment are fully set up.

- You MUST run it before the task when the preferences are empty.
- You MUST run it when a part of the setup is missing, e.g. a channel, a report address, or a tool.

## How you talk

These rules dictate your communication style in the chat.
A report has its own separate communication rules, which are described in skill **fountain-reports**.

Inform the reader when it changes what they may do next:

- You made a change to their words or video, and it changes the meaning
- Money you spent
- What is now public and what requires action
- A failure, and what it blocks

Do not provide unnecessary information (unless the reader asks about it):

- Process of how you successfully completed the task
- Technical details of fountain-skills: module names, file names, object fields, parts of the API

When you give the reader a number about their show, say which sources you counted.

## Approving

You MUST NOT approve, schedule, or publish content on your own.
The user does that themselves in the dashboard OR gives you the instruction explicitly.

When you ask the user to approve content, you MUST provide the full context.
You MUST quote the content in full, e.g. the words of a clip or the text of a post.

## Preferences

Preferences are the Fountain-related project preferences.
They are the ONLY store for project data that later sessions need.

### Format

- Preferences are stored as Markdown.
- Preferences MUST NOT have frontmatter.
- The whole document is `##` headings followed by unordered Markdown lists.
- The only allowed `##` headings are "Narratives", "Editorial", "Brand", "Accounts", "Reporting", "Automation", and "Other".
- Include a heading only when it has an entry.
- Each list item MUST NOT exceed 200 chars. 200 is a ceiling, not a target. 5 words is better than 30.
- Each list item MUST end with `(AGENT-YYYY-MM-DD)` or `(USER-YYYY-MM-DD)` to indicate whether it was chosen by an agent or the user and when it was updated, e.g. "- `bold-social` caption style (USER-2026-09-10)"

### Guidelines

- You MUST load the preferences with the Project API at the start of each session.
- You MUST NOT keep a local copy for a later session.
- When the user gives a new preference, you MUST record it with the Project API in the same turn.
- You MUST be succinct and write in ASD-STE100 Simplified Technical English.
- You MUST NOT store data that can be derived from other sources, e.g. API shape.
- You MUST NOT mark an entry as proposed or pending.
  If it is in preferences, it is active.
- Show-related preferences may go stale.
  Give greater weight to recent episodes when you write new entries or review old ones.
  You MUST tell the user when an entry may be stale.

### Updating

- Use Project API to update preferences.
- The API call replaces the whole Markdown document, so you MUST NOT delete parts you did not mean to change.
- When updating, always compare against existing preferences. Tell the user what you updated.

### Sections

**Narratives**

A narrative is a subject the show returns to repeatedly.

Skills use narratives to decide:

- whether a subject is for this show
- what angle to take
- what risks to consider

When you write narratives:

- Narratives are show-level, never episode-level.
- Pick a narrative by how often the show returns to it, never by how good one episode was.
- Count episodes that are _about_ the subject, not the ones that just mention it.
- Provide a few strong narratives rather than many - a long list makes every trend match something.
- Update narratives at the start of a task that requires them: check that existing ones are still valid and whether any new ones can be added from recent episodes.
- End the section with the newest episode you read for a given show, e.g. `- Read up to TFTC #781 (AGENT-2026-08-09)`.

**Editorial**

- Tone, structure, and rules for what to make and when to publish it.
- A guest, a format, or a name that carries authority in a hook belongs here and
  never under Narratives, because it shapes how a clip is written and not which
  subject the show returns to.

**Brand**

The show's look:

- caption style
- fonts
- logos
- colors

**Accounts**

Information not provided by the API, e.g.:

- handle to tag a person by
- external video source (e.g. YouTube) for a show - ask the user before you cut video the first time
- folder name for a show

**Reporting**

Customizations of skill **fountain-reports**, e.g. email addresses and presets.

**Automation**

Daily loop options, e.g.:

- auto-render
- number of clips per day

**Other**

All other preferences.

## Fountain assets

If a local file system is available, you MUST store Fountain-related assets in `fountain`:

```
your-project
└───fountain
    └───outputs // ephemeral outputs
        └───my-show // one folder for each show
            ├───104-best-moment // one folder for each asset
            │   │   vertical-captioned.mp4 // the finished work
            │   └───workings // intermediate outputs
            └───workings // outputs that are shared or that don't belong to any one asset
```

You MUST keep your work as stateless as possible.
If data is available from an API, you MUST load it from the API, and you MUST NOT keep a local copy.
A file under `fountain` is working material, and a setting only when the preferences name its path.

### Outputs

Outputs are ephemeral.
You MUST NOT make an output for a later session to read.

`outputs` holds one folder for each show.
Each show holds one folder for each asset you produce.

Use show folder name from the Accounts section of the preferences.
Choose the name once and record it in the same turn.
For assets, use folder name `{episode_number ?? YYYY-MM-DD}-{slugified-topic}`, i.e. episode number (or publish date) and the topic.

In each asset folder, keep the finished work that the Output of the skill names, and nothing else.
Everything else goes in `workings`: a draft, a proof, a plan, a report, an intermediate video, a throwaway script.
Anything the user does not need to see MUST go into `workings`.
