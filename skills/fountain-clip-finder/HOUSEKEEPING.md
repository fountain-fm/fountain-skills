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

Preferences are stored as Markdown.
It MUST NOT have frontmatter.

### Guidelines

- You MUST load the preferences with the Project API at the start of each session.
- You MUST NOT keep a local copy for a later session.
- When the user gives a new preference, you MUST record it with the Project API in the same turn.
- You MUST be succinct.
- Clearly mark when a preference is only proposed - let the user decide whether to keep it.
- Clearly mark a preference you chose yourself. It MUST be obvious when it was not an explicit choice by the user.
- Show-related preferences may go stale.
  Give greater weight to recent episodes when you write new entries or review old ones.
  You MUST tell the user when an entry may be stale.

### Updating

- Use Project API to update preferences.
- The API call replaces the whole Markdown document, so you MUST NOT delete parts you did not mean to change.
- When updating, always compare against existing preferences. Tell the user what you updated.

### H2 (##) headings

You MUST use only these headings:

- Narratives - the subjects the show returns to, each with its angle and risks to avoid.
- Editorial - tone, structure, and rules for what to make and when to publish it.
  A guest, a format, or a name that carries authority in a hook belongs here and never under
  Narratives, because it shapes how a clip is written and not which subject the show returns to.
- Brand - the show's look: caption style, fonts, logos, and colours.
- Accounts - information not provided by the API: handle to tag a person by,
  external video source (e.g. YouTube) for a show, and the folder name for a show.
- Reporting - email addresses reports go to and preset customizations of skill **fountain-reports**.
- Automation - daily loop options, e.g. auto-render and the day's clip budget.
- Other - all other preferences.

Write a heading only when it has an entry.

Empty preferences mean a new project, so follow the first contact steps of skill **fountain-reports**.
When you rely on a built-in default because no setting names a choice, say so in passing.

Accounts MUST name where the show's video lives before you count or cut anything from video.
Ask the user when it says nothing, and record that Fountain holds it all when that is the answer.

### Narratives

A narrative is a subject the show returns to, with the angle the show takes and the risks to avoid.
It is how a skill decides whether a subject is for this show, and how it shapes what it makes of it.
Write one line for each, in that order.
Pitch it between the show and one episode: the subject of the whole show fits every story, and the
subject of one episode fits only that one.
A narrative earns its place by how often the show returns to it, and never by how good one episode was.
Count the episodes that are about a subject, and not the ones that mention it, because a passing
mention is not coverage and a keyword search cannot tell the two apart.
Give few strong narratives rather than many, because a long list makes every trend match something.

Bring this section level with the show before you read it, whichever skill you are running.
It records the newest episode it has read: build it from the episode titles of the Content API when
it records none, whatever entries it already holds, and fold in the later episodes otherwise.
Add a narrative when an episode fits none.
End the section with the newest episode you read, named the way the show names it, e.g.
`Read up to #781, 2026-08-09.`
A sentence about where the entries came from is not that line, and the next run rebuilds without it.

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
