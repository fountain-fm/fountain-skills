This housekeeping file is the same for every Fountain skill. It is enough to read it once per session.

## What you say

The reader makes podcasts, and does not work on this software.
This section is what you say in the chat; a report has its own shape, and skill **fountain-reports**
owns it.

Say a thing when it changes what the reader does next:

- A change you made to their words or their video, when it changes the meaning.
- A choice that is theirs, with the options made plain.
- Money you spent.
- What is now public, what waits for them, and what moves only when they act.
- A failure, and what it stops.

Leave out a step that worked, a number that only proves the work happened, and a name from inside
this software, such as a module, a field, or a part of the API.
Name a file only when the reader opens it, and put everything that worked in one line.

Never ask the reader to approve a thing without putting the words they are approving in front of them.

## Preferences

Preferences are the Fountain-skills-related user preferences.
They are the ONLY store for user data that later sessions need.

You MUST load the preferences with the Project API of skill **fountain-api** at the start of each session.
When the user gives a new preference, you MUST record it with the Project API in the same turn.
You MUST mark a preference that the user did not give as proposed, and let them keep it or cut it.
An entry you derive from the show goes stale as the show changes, so weigh the recent episodes above
the old ones whenever you write one, and not only under Narratives.
Say so when you notice an entry the show has outgrown, because nothing else will tell the user.
A write replaces the whole document, so you MUST carry every entry and mark you did not mean to change.
You MUST be succinct.
You MUST NOT keep a local copy for a later session.

Preferences are stored as Markdown.
It MUST NOT have frontmatter.

### H2 (##) headings

You MUST use only these headings:

- Narratives - the subjects the show returns to, each with its angle and the risk to avoid.
- Editorial - tone, structure, and rules for what to make and when to publish it.
  A guest, a format, or a name that carries authority in a hook belongs here and never under
  Narratives, because it shapes how a clip is written and not which subject the show returns to.
- Brand - the show's look: caption style, fonts, logos, and colours.
- Accounts - what the API cannot name: the handle to tag a person by, where a show's video lives, and
  the folder name of a show.
- Reporting - how the user wants their reports and emails: preset customizations of skill **fountain-reports**.
- Automation - the switches of the daily loop, e.g. auto-render and the day's clip budget.
- Other - all other preferences.

Write a heading only when it has an entry.
An absent heading means the same as an empty one, and this list is the place that names what can exist.

Empty preferences mean a new project, so follow the first contact steps of skill **fountain-reports**.
When you rely on a built-in default because no setting names a choice, say so in passing.

### Narratives

A narrative is a subject the show returns to, with the angle the show takes and the risk to avoid.
It is how a skill decides whether a subject is for this show, and how it shapes what it makes of it.
Write one line for each, in that order.
Pitch it between the show and one episode: the subject of the whole show fits every story, and the
subject of one episode fits only that one.
A narrative earns its place by how often the show returns to it, and never by how good one episode was.
A subject the show keeps returning to this year is a narrative whatever its share of the decade, and
one it has stopped covering is not a narrative any more.
Count the episodes that are about a subject, and not the ones that mention it, because a passing
mention is not coverage and a keyword search cannot tell the two apart.
Give few strong narratives rather than many, because a long list makes every trend match something.
A guest is not a narrative, and neither is a format.

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
    │   LOG.md // daily log, optional
    └───outputs // ephemeral outputs
        └───my-show // one folder for each show
            ├───104-best-moment // one folder for each thing you make
            │   │   vertical-captioned.mp4 // the finished work
            │   └───workings // what that thing was made from
            └───workings // workings that belong to no one thing
```

You MUST keep your work as stateless as possible.
If data is available from an API, you MUST load it from the API, and you MUST NOT keep a local copy.

### LOG.md

You MUST keep this if a local file system is available.
It can help with debugging for yourself, the user, and Fountain support.

When you use Fountain skills, record what you do in this file after each turn.
You MUST NOT read this file in full, just the latest 7 days at the end of the file.

#### H2 (##) headings

MUST follow `## YYYY-MM-DD` format.
The oldest day MUST be first.

#### Body

Under today's heading, record one Markdown list item at the end of the turn.
This MUST include your actions, as well as new findings and failures if any.
You MUST be succinct.

### Outputs

Outputs are ephemeral.
You MUST NOT make an output for a later session to read.

`outputs` holds one folder for each show, and each show holds one folder for each thing you make.
Neither holds a loose file.

Take the name of a show folder from the Accounts section of the preferences, and keep it short.
Choose one the first time you make that folder, and record it there in the same turn, or the next run
picks a different name and splits one show in two.
Name a thing for the episode and then the thing, e.g. `104-best-moment`.
Use the day the episode came out when the show does not name its episodes.

In the folder of a thing, keep the finished work that the Output of the skill names, and nothing else.
Name each file for what it is, because the folder already says which thing it belongs to.
Everything else goes in `workings`: a draft, a proof, a plan, a report, an intermediate video, and
any file a script wrote for another script.
Workings that belong to no one thing go in the `workings` of the show.
Put a file in `workings` when you are not sure.

A user who opens a folder MUST see their work, and MUST NOT see how it was made.

## Fountain API

Skill **fountain-api** is the ONLY way to interact with the Fountain API.
