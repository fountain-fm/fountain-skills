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

- The `SocialPostMediaSource` of the verified clip.
- The name the caller asked for, when the request named a person.
- The scores from module **discovery** and module **boundaries**, and each flag.
- The show's connected channels, via the Social API.
- Voice notes from the Editorial section and confirmed handles from the Accounts section of the preferences.
- The trend and its sources, when a caller found the clip for a news story.

## Output

- `content.title` - a short title in the quote format, for the dashboard and the email digest.
- `context` - a Markdown note that gives the reason to post the clip.
- `content.text` - one text per `SocialPlatform` the clip suits.
- The risk flags, with each new flag that the copy itself introduces.

## Requirements

- Fountain API.

## Process

1. Read the Narratives and Editorial sections of the preferences.
   Treat them as rules to follow, not as background.
2. Write the title in this format:

   ```text
   "<quote>" — <person> on <topic>
   "Nobody wants to say it out loud" — <person> on <topic>
   ```

   The quote is at most 40 characters, and the full title is at most 90 characters.
   `<person>` is the speaker, named as the show credits them.
   The transcript names nobody, so the guest is a guess whenever the host may have said the line.
   Say which words you are unsure of, and skill **fountain-clip-producer** settles it on the video.
   `<topic>` is 1 to 4 words that say what the quote is about.

3. Write the context note in Markdown, 300 to 1200 characters, and give it no heading of its own:
   the dashboard labels the note where the user reads it, so a heading arrives twice.
   The ceiling came down when the sources moved into the prose, because a note that long was mostly
   links and the checks behind the clip.

   - What happened in the news and why it is live today, when the clip answers a trend.
   - What the clip contains, and the claim the speaker makes.
   - Why the clip answers that story, and which score dimension made it win.
   - A risk the user has to weigh, in one sentence, and nothing when the clip carries none.

4. Write `content.text` for each `SocialPlatform` the clip suits.
   Match the length, the tone, and the conventions of that platform.
   Write one text per platform, and never reuse one text across platforms.
5. Name the speaker who is on camera.
   Read the handle from the Accounts section of the preferences, or from the episode show notes with the Content API.
6. Run the safety pass over every text before you return it.

## Additional notes

Title rules:

- Copy the quote from `transcript` word for word, and do not correct the grammar.
  Put a word heard wrong right in `transcript` itself, and not only in the quote you took from it,
  because the user reads the clip against `transcript` and the two MUST agree.
  Do it before the post exists, and on the post when you find it later - the span cannot change, so
  only the words can be put right.
- Cut a long quote at a word break, and never add an ellipsis to reach the limit.
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
- Say nothing about a risk the clip does not carry, and nothing about the checks you ran.
  That the speaker was confirmed on the render, that no advertisement sits in the span, that the hook
  is a little soft, that nothing dates - these are how the work was done, and the user decides nothing
  from them.

Source rules, for a clip that answers a news story:

- Link the source inside the sentence that uses it, and name the publication in the words around it,
  e.g. "The Times reported on Tuesday that [the Fed raised rates](url)".
  Never end the note with a list of links: a reader follows a source to check a claim, so it belongs
  where the claim is.
- Cite one source, the most reputable that carries the story, and add another only where it tells the
  reader something the first does not.
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
- Never write a quote or a statistic that `transcript` does not hold.

Speaker naming:

- Confirm who is on camera, because a show with two hosts often cuts to the other person.
- A handle is confirmed when the episode's show notes give it as a link, or when Accounts holds one
  the user gave.
  Never record a guest's handle: read it from the notes of the episode you are clipping, because it
  belongs to that episode.
  Record the show's own handle or a host's under Accounts when the notes do not give it and the user
  does.
- Credit the speaker by name when no handle is confirmed for that platform.
- Never guess a handle, and never use one platform's handle on another.

Copy that changes what the speaker means is a failure, however well it reads.
