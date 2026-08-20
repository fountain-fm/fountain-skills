<!-- Data: one card per clip, rendered or not - title, duration, platform, timecode, preview_url, -->
<!-- context, text, transcript, flags. One card carries every platform the clip goes to, with the -->
<!-- copy of each, because the reader reviews a clip and not a post. -->
<!-- context is the note the post already carries: what happened in the news, what the clip says, why -->
<!-- it answers that story, and the sources as links. It is written once and stored on the post, so -->
<!-- the report shows it and never rewrites it. -->
<!-- text is content.text, the copy that goes out, labelled per platform when they differ. -->
<!-- transcript is source.transcript, quoted whole, so the reader reads the words that were said. -->
<!-- preview_url plays the episode from the moment, so the reader can check it. -->
<!-- flags lists each risk flag, or "none". Drop a line whose data the caller did not give. -->
<!-- The title links to the post in the dashboard: show_id is the ContentID of the show, one of -->
<!-- ProjectOverview.shows, and post_id is the id of the SocialPost. Same domain rule as dashboard-link. -->

### [{title}](https://beta.fountain.fm/studio/{show_id}/posts/{post_id})

{duration} - {platform} - [watch from {timecode}]({preview_url})

{context}

{text}

> {transcript}

Flags: {flags}
