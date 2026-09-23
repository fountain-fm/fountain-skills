---
name: copy
description: Write the label, the context note, and the platform post text for a verified clip, and check them for risk.
---

## Overview

A verified moment is not yet a post, because the clip has no words of its own.
The preferences hold the voice of the show, and this module applies that voice to each platform in turn.
A safe clip can still become an unsafe post, so this module runs the risk check on the finished words.
The words MUST agree with the clip.
If the words promise something that the clip does not give, the viewer leaves at once.

## Input

- The `SocialPostMediaSource` of the verified clip, or the external source of a raw local video.
- The title of an external video from module **external-source**.
- The name the caller asked for, when the request named a person.
- The link that every post MUST carry, when the caller gives one.
- The scores from module **discovery** and module **boundaries**, and each flag.
- The show's connected channels, via the Social API.
- Voice notes from the Editorial section and handles from the Accounts section of the preferences.
- The trend and its sources, when a caller found the clip for a news story.

## Output

- `meta.label` - a short internal label in the quote format, the same on every channel of the clip.
- `context` - a Markdown note that gives the reason to post the clip.
- `content.text` - one text per `SocialPlatform` the clip suits.
- `content.title` - only for a platform that shows a title beside the text, e.g. YouTube.
- The risk flags, with each new flag that the copy itself introduces.

## Requirements

- Fountain API.

## Process

1. Read the Narratives and Editorial sections of the preferences.
   Treat them as rules to follow, not as background.
2. Write the label in this format:

   ```text
   "<quote>" — <person> on <topic>
   "Nobody wants to say it out loud" — <person> on <topic>
   ```

   The quote is at most 40 characters, and the full label is at most 90 characters.
   `<person>` is the speaker, named as the show credits them.
   The transcript names no speaker.
   Thus the guest name is a guess whenever the host may have said the line.
   Say which words you are unsure of.
   Skill **fountain-clip-producer** resolves the uncertainty on the video.
   `<topic>` is 1 to 4 words that say what the quote is about.

3. Write the context note in Markdown, with 300 to 1000 characters of the words that the reader sees.
   Give the note no heading of its own.
   The dashboard labels the note where the user reads it, so a heading would show twice.
   The reader approves one clip and moves to the next, so the reader reads the note in a few seconds.
   The count MUST include only the link text, and not the URL address after it.

   - What happened in the news and why it is live today, when the clip answers a trend.
   - What the clip contains, and the claim the speaker makes.
   - Why the clip answers that story, and which score dimension made it win.
   - The external video title, when `ids` does not name an episode.
   - A risk the user has to weigh, in one sentence, and nothing when the clip carries none.

4. Write `content.text` for each `SocialPlatform` the clip suits.
   Match the length, the tone, and the conventions of that platform.
   Write one text per platform, and never reuse one text across platforms.
   Write `content.title` only where the platform shows a title.
   The title must make the viewer want to watch, and it must describe the clip accurately.
   Follow the usual rules of the platform, such as a short length, the important words first, and few
   capitals or emoji.
   Put the link that the caller gave at the end of the text, on its own line.
   Write the address exactly as the caller gave it.
   A campaign reads the parameters of that address, and a shortened or cleaned-up address is a different link.
5. Name the speaker who is on camera.
   Read the handle from the Accounts section of the preferences, or from the episode show notes with the Content API.
   A clip from a video that Fountain does not hold has no show notes.
   Thus the only sources are the video title and the preferences, and no other source confirms a handle.
6. Run the safety pass over every text before you return it.

## Additional notes

Label rules:

- Copy the quote from `transcript` word for word, and do not correct the grammar.
  Correct a misheard word in `transcript` itself, and not only in the quote that you took from it.
  The user compares the clip with `transcript`, and the two MUST agree.
  Make the correction before the post exists.
  If you find the error later, correct it on the post.
  The span cannot change, so only the words can be corrected.
- Cut a long quote at a word break, and never add an ellipsis to reach the limit.
- A quote from an automatic caption track or a whisper transcript is a machine transcription of the words.
  Say that the quote needs confirmation from the render.
  Never quote a name or a number from such a source without saying so.
  A subtitle file that the show wrote itself is not a machine transcription, and needs no such warning.
- Use sentence case, and no emoji, no hashtag, and no clickbait question.
- Name the moment, and not the episode.

Context rules:

- Write statements, and not marketing language.
- Name the score dimension, for example "it wins on controversy".
- Do not repeat the post text, because the two have different readers.
- Name a risk the user has to weigh: a claim about a named person, a legal or medical exposure,
  political language, a dated prediction inside the span, an `already-clipped` moment, or a video
  match that is not `high`.
  Write it as one sentence in the prose, and never as a list under a heading of its own.
- Say nothing about a risk that the clip does not have, and nothing about the checks that you ran.
  Do not say that the render confirmed the speaker, or that no advertisement is in the span.
  Do not say that the hook is a little weak, or that nothing in the clip will become dated.
  These details tell how the work was done, and the user makes no decision from them.

Source rules, for a clip that answers a news story:

- Link the source inside the sentence that uses it, and name the publication in the words around it,
  e.g. "The Times reported on Tuesday that [the Fed raised rates](url)".
  Never end the note with a list of links.
  A reader follows a source to check a claim, so put the source where the claim is.
- Cite one source, the most reputable one that reports the story.
  Add another source only where it tells the reader something that the first source does not.
- A source MUST be published in the last 48 hours.
- Use a publication that has an editorial standard.
  Do not cite a social post, an aggregator, or a blog with no named author.
- You MUST NOT invent a source, a headline, or a date.
- When no source meets these rules, say that the clip is evergreen, and do not claim that it is timely.

Safety pass:

- Keep each risk flag from module **discovery**, and never remove one without saying so.
- Use the higher-risk list of module **discovery**.
  Add a flag when the copy introduces a trigger that the clip itself did not hold.
- Change higher-risk wording into a question, and flag it for the user to clear.
- Remove copy that you cannot make safe.
  Do not soften it into something that misleads.
- Never say that the guest answers today's news unless the recording is later than the event.
- Never write a quote or a statistic that `transcript` does not hold.

Speaker naming:

- Confirm who is on camera, because a show with two hosts often cuts to the other person.
- A handle is confirmed when the episode's show notes give it as a link, or when Accounts holds one
  the user gave.
  Never record a guest's handle.
  Read it from the notes of the episode that you are clipping, because the handle belongs to that episode.
  Record the show's own handle or a host's handle under Accounts when the notes do not give it but the
  user does.
- Credit the speaker by name when no handle is confirmed for that platform.
- Never guess a handle, and never use one platform's handle on another.

Copy that changes the meaning of the speaker is a failure, even when it reads well.
