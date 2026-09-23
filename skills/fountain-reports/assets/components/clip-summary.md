<!-- Data: one entry per clip - label, post_url, source, source_published, channels. -->
<!-- A summary for a report that sends the reader to the dashboard. -->
<!-- It gives enough to recognise a clip. -->
<!-- It never gives the copy or the transcript, because the reader reads those in the dashboard. -->
<!-- source names the episode or external video that the clip was cut from. -->
<!-- source_published includes its short publish date in parentheses when known, e.g. (20 May 2026). -->
<!-- A clip can be cut from a source of any age, and the reader judges an old moment differently. -->
<!-- channels lists every channel the clip went to, because a clip is one post on each of them. -->
<!-- The label links to the post of the first channel listed, so post_url is that post's link. -->
<!-- The summary is quoted for the same reason as a performance card. -->
<!-- A quote is the only container that Markdown can make, and every clip in a report is held the same way. -->
<!-- The two lines have no blank line between them. -->
<!-- A blank line ends a quote, and would give the reader two containers that each hold half a clip. -->

> ### [{label}]({post_url})
>
> {source}{source_published} - {channels}
