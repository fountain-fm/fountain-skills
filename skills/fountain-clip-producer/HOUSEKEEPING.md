## Overview

This housekeeping file is the same for every Fountain skill.
It is enough to read it once per session.

The reader does not develop fountain-skills.

## About fountain-skills

Fountain makes clips on its servers, with no agent.

- Automations are project settings in `settings.workflows` of the `ProjectOverview`.
  E.g. with Daily Growth on, Fountain matches the news of each day to the archive of each show.
  Then it makes draft clip posts, renders their videos, and emails a report.
- Fountain renders the video of each new clip post automatically.
- On request, it renders a clip again with a prompt for the change, e.g. "bigger captions".

The skills set up Fountain, and help the user to use it well.
Do all other work with the API directly, e.g. edit the text of a draft, or turn an automation on or off.

Fountain has an MCP that wraps around its API.

github.com/fountain-fm/fountain-skills contains

- all the skills (including this file)
- the configuration files for the MCP and the agent plugins

A plugin is a package that contains

1. the MCP
2. the skills

The plugin is the preferred way to install Fountain MCP and skills.
The reason is that the plugin receives regular updates.

### API

The API can

- load project information
- load public shows, episodes, and transcripts
- search across public content and transcripts
- publish your podcasts
- make, render, and publish social posts

An agent reaches the API through one of two routes.

#### Route A: MCP (preferred)

- MCP enables Fountain users to authenticate via OAuth instead of generating API keys
- MCP provides one tool for each API endpoint
- For more information, you can read the docs at https://fountain.fm/docs.md
- If MCP is not connected, ask the user to connect it via the MCP Server URL

Config:

- Server URL: https://api.fountain.fm/v1/mcp
- Authorization: Fountain User OAuth

#### Route B: HTTP (discouraged)

- MUST read https://fountain.fm/docs.md in each new session
- Find the API key in the `FOUNTAIN_API_KEY` environment variable or in `.env`
- If no key, ask the user to make one at https://fountain.fm/studio/projects
- A Fountain key starts with `fountain_`.
  If a request fails to authenticate and the key has a different prefix, the key is for another service.
  You MUST tell the user.
- You MUST NOT write the key into a log, a command, a report, or any file other than the key store.

Config:

- Base URL: https://api.fountain.fm/v1
- Authorization: Fountain API Key as Bearer Key

#### Additional details

- If you think that the MCP/API is not connected or not authenticated, try to list the projects to check.
  Do not assume that the MCP/API does not work before you do this check.
- Write a large response to a file and read only the part you need.
- You CAN write a throwaway script, e.g. to repeat one request over many items.
  Put it in a temporary place and delete it at the end of the session.
  You MUST NOT keep a script that wraps the API, because the API can change.

### Clips

Fountain renders the video of each clip post automatically, when the post has a `source` and no upload.
The Social API gives the state of each render.
Always give the `post_url` of each post that you tell the user about.

To change the look of a clip, render it again with the Social API, and give the change as a prompt.
The new video replaces the video of each unpublished post that shares the clip.
A change for all later clips belongs under Brand, because each render reads the preferences.

Always prefer a Fountain render, also when Fountain cannot render all of a request, e.g. a logo.
Say what Fountain cannot render, and offer the closest look that it can, from the clip rendering page.
Use skill **fountain-clip-producer** only when the user asks for a render on their own computer.

## Setup

Skill **fountain-onboarding** sets up Fountain and the preferences.

- You MUST run it before the task when the user has no project, no show, or no connected channel.
- Suggest it when the preferences have no caption style.
  Fountain renders with its default style until the user chooses one.

## How you talk

These rules tell you how to communicate in the chat.

Tell the reader about each of these items when the item changes what the reader may do next:

- A change that you made to their words or video, when the change alters the meaning
- Money you spent
- What is now public and what requires action
- A failure, and what it blocks

Do not give unnecessary information, unless the reader asks for it:

- The steps that you took to complete the task successfully
- Technical details of fountain-skills: module names, file names, object fields, parts of the API

When you give the reader a number about their show, say which sources you counted.

## Approving

You MUST NOT approve, schedule, or publish content on your own.
The user does these actions in the dashboard, OR the user explicitly tells you to do them.

When you ask the user to approve content, you MUST provide the full context.
You MUST quote the content in full, e.g. the words of a clip or the text of a post.

## Links

- `post_url` - `https://fountain.fm/studio/{project_id}/~/posts/{post_id}`
- `drafts_url` - `https://fountain.fm/studio/{project_id}/~/posts?tab=DRAFT`
- Clip rendering page - `https://fountain.fm/docs/rendering-clips`
  Read its text at `https://fountain.fm/docs/rendering-clips.md`.

## Preferences

Preferences are the Fountain-related project preferences.
They are the ONLY store for project data that later sessions need.

### Format

- Preferences are stored as Markdown.
- Preferences MUST NOT have frontmatter.
- The whole document is `##` headings followed by unordered Markdown lists.
- The only allowed `##` headings are "Narratives", "Editorial", "Brand", "Accounts", and "Other".
- Include a heading only when it has an entry.
- Each list item MUST NOT exceed 200 chars.
  200 is a maximum, not a target.
  5 words is better than 30.
- Each list item MUST end with `(AGENT-YYYY-MM-DD)` or `(USER-YYYY-MM-DD)`.
  This tag shows whether an agent or the user chose the item, and when the item was updated.
  E.g. "- `bold-social` caption style (USER-2026-09-10)"
- An older document can have a Reporting or an Automation section.
  No part of Fountain reads them, so remove them when you next update the preferences.
  Tell the user what you removed.

### Guidelines

- You MUST load the preferences with the Project API at the start of each session.
- You MUST NOT keep a local copy for a later session.
- When the user gives a new preference, you MUST record it with the Project API in the same turn.
- You MUST be succinct and write in ASD-STE100 Simplified Technical English.
- You MUST NOT store data that can be derived from other sources, e.g. API shape.
- You MUST NOT mark an entry as proposed or pending.
  If it is in preferences, it is active.
- Show-related preferences may go stale.
  Give more weight to recent episodes when you write new entries or review old ones.
  You MUST tell the user when an entry may be stale.

### Updating

- Use Project API to update preferences.
- The API call replaces the whole Markdown document.
  Thus you MUST NOT delete parts that you did not mean to change.
- When you update, always compare against the existing preferences.
  Tell the user what you updated.

### Sections

**Narratives**

A narrative is a subject the show returns to repeatedly.
Daily Growth uses narratives to choose the angle of a clip.
When Daily Growth runs for a show that has no narratives, it writes the first ones.

- Narratives are show-level, never episode-level.
- A narrative for one show starts with the show ID, e.g.
  `- show:id:abc123 — Bitcoin mining and energy (AGENT-2026-10-26)`.
  Put one space on each side of the dash, or Fountain reads the entry as one for each show.
  A narrative without a show ID is for each show of the project.
  When the project has more than one show, add the show ID to each older entry that is for one show only.
- Pick a narrative by how often the show returns to it, never by how good one episode was.
- Count episodes that are _about_ the subject, not the ones that just mention it.
- Give a few strong narratives rather than many.
  A long list makes every news story match something.

**Editorial**

- Tone, structure, and rules for the words of a post, e.g. "never use emoji".
- A guest, a format, or a name that makes a hook more credible belongs here, and never under Narratives.
  The reason is that such an item changes how a clip is written, and not which subject the show returns to.

**Brand**

The show's look: caption style, colors, fonts, and logos.
Each render reads this section, so a change applies from the next render.
To apply a change to a clip that exists, render it again.

**Accounts**

Information that the API does not provide, e.g.:

- the handle to use when you tag a person
- the YouTube channel of a show, when its video is not on Fountain

**Other**

All other preferences.
