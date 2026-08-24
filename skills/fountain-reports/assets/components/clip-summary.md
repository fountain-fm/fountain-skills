<!-- Data: one entry per clip - title, episode, channels, show_id, post_id. -->
<!-- A summary for a report that sends the reader to the dashboard: enough to recognise a clip, and -->
<!-- never the copy or the transcript, which component candidate-card carries for a review by email. -->
<!-- episode names the episode the clip was cut from, the way the show names it, e.g. #748. -->
<!-- episode_published is the day that episode came out, short, e.g. 20 May 2026. A clip can be cut -->
<!-- from an episode of any age, and the reader judges it differently when it is three months old. -->
<!-- channels lists every channel the clip went to, because a clip is one post on each of them. -->
<!-- The title links to the post in the dashboard: post_id is the post of the first channel listed. -->
<!-- The summary is quoted for the same reason a performance card is: it is the only container -->
<!-- Markdown can make, and every clip in a report is held the same way. -->

> ### [{title}](https://beta.fountain.fm/studio/{show_id}/posts/{post_id})

> {episode} ({episode_published}) - {channels}
