---
name: copy
description: Write the title, the context note, and the platform post text for a verified clip, and check them for risk.
---

## Overview

A verified moment is not yet a post, because the clip carries no words of its own.
The show's voice lives in the preferences, and this module applies that voice to each platform in turn.
A safe clip can still become an unsafe post, so the risk check runs on the finished words.
The words MUST agree with the clip, because a promise the clip does not keep loses the viewer at once.

## Input

- The verified clip: `content_id`, `start_time_seconds`, `end_time_seconds`, and `transcript`.
- The speaker's confirmed name and synonyms from module **discovery**, when it resolved a person.
- The scores from module **discovery** and module **boundaries**, and each flag.
- The show's platforms, voice notes, and confirmed handles from the preferences.
- The trend and its sources, when a caller found the clip for a news story.

## Output

- `title` - a short title in the quote format, for the dashboard and the email digest.
- `context` - a Markdown note that gives the reason to post the clip.
- `post_text` - one text per platform the clip suits.
- The risk flags, with each new flag that the copy itself introduces.

## Requirements

- Skill **fountain-api**.

## Process

1. Load skill **fountain-api** and read the Narratives and Editorial sections of the preferences.
   Treat them as rules to follow, not as background.
2. Write the title in this format:

   ```text
   "<quote>" — <person> on <topic>
   "Nobody wants to say it out loud" — Eric Voskuil on Bitcoin custody
   ```

   The quote is at most 40 characters, and the full title is at most 90 characters.
   `<person>` is the speaker, named as the show credits them.
   `<topic>` is 1 to 4 words that say what the quote is about.

3. Write the context note in Markdown, 300 to 1200 characters, under the heading `## Why this clip`:

   - What the clip contains, and the claim the speaker makes.
   - Why the clip is strong, and which score dimension made it win.
   - For a news story only: what happened, why the clip matters now, and at least one source.

4. Write the post text for each platform the clip suits.
   Match the length, the tone, and the conventions of that platform.
   Write one text per platform, and never reuse one text across platforms.
5. Name the speaker who is on camera.
   Read the handle from the Other section of the preferences, or from the episode show notes with the Content API.
6. Run the safety pass over every text before you return it.

## Additional notes

Title rules:

- Copy the quote from the transcript word for word, and do not correct the grammar.
- Cut a long quote at a word break, and never add an ellipsis to reach the limit.
- Use sentence case, and no emoji, no hashtag, and no clickbait question.
- Name the moment, and not the episode.

Context rules:

- Write statements, and not marketing language.
- Name the score dimension, for example "it wins on controversy".
- Do not repeat the post text, because the two have different readers.
- Name each risk flag, an `already-clipped` moment, and a video match that is not `high`.
  The user decides from this note, so anything it does not name is something nobody sees.

Source rules, for a clip that answers a news story:

- Cite each source as a Markdown link, and name the publication in the link text.
- A source MUST be published in the last 48 hours.
- Use a publication that has an editorial standard.
  Do not cite a social post, an aggregator, or a blog with no named author.
- You MUST NOT invent a source, a headline, or a date.
- Say that the clip is evergreen when no source holds, and do not claim that it is timely.

Safety pass:

- Carry each risk flag from module **discovery** forward, and never drop one in silence.
- Use the higher-risk list of module **discovery**.
  Add a flag when the copy introduces a trigger that the clip itself did not hold.
- Change higher-risk wording into a question, and flag it for the user to clear.
- Drop copy that you cannot make safe, and do not soften it into something that misleads.
- Never say that the guest answers today's news unless the recording is later than the event.
- Never write a quote or a statistic that the transcript does not hold.

Speaker naming:

- Confirm who is on camera, because a show with two hosts often cuts to the other person.
- Credit the speaker by name when no handle is confirmed for that platform.
- Never guess a handle, and never use one platform's handle on another.

Copy that changes what the speaker means is a failure, however well it reads.
