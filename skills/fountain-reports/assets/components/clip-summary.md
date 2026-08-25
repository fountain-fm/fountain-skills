<!-- Data: one entry per clip - title, post_url, episode, channels. Build the link from links.md. -->
<!-- A summary for a report that sends the reader to the dashboard: enough to recognise a clip, and -->
<!-- never the copy or the transcript, which the reader reads in the dashboard. -->
<!-- episode names the episode the clip was cut from, the way the show names it, e.g. #748. -->
<!-- episode_published is the day that episode came out, short, e.g. 20 May 2026. A clip can be cut -->
<!-- from an episode of any age, and the reader judges it differently when it is three months old. -->
<!-- channels lists every channel the clip went to, because a clip is one post on each of them. -->
<!-- The title links to the post of the first channel listed, so post_url is that post's link. -->
<!-- The summary is quoted for the same reason a performance card is: it is the only container -->
<!-- Markdown can make, and every clip in a report is held the same way. -->
<!-- The two lines carry no blank line between them, because a blank line ends a quote and would -->
<!-- give the reader two containers holding half a clip each. -->

> ### [{title}]({post_url})
>
> {episode} ({episode_published}) - {channels}
