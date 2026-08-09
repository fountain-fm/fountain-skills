<!-- Data: one card per clip, rendered or not - title, duration, platform, timecode, preview_url, -->
<!-- why_now, text, transcript, sources, flags. One card carries every platform the clip goes to, -->
<!-- with the copy of each, because the reader reviews a clip and not a post. -->
<!-- why_now is the "Why this clip" note the post already carries; text is content.text, the copy that -->
<!-- goes out, labelled per platform when they differ; transcript is source.transcript, quoted whole so -->
<!-- the reader reads the words that were said; preview_url plays the episode from the moment, so the -->
<!-- reader can check it; sources are the news items that made the trend live, each with its publisher, -->
<!-- or "none" for a clip that answers no trend; flags lists each risk flag, or "none". -->
<!-- Drop a line whose data the caller did not give. -->

### {title}

{duration} - {platform} - [watch from {timecode}]({preview_url})

{why_now}

{text}

> {transcript}

Sources: {sources}

Flags: {flags}
