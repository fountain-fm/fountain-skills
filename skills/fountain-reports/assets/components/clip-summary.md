<!-- Data: one entry per clip - label, post_url, source, source_published, channels. -->
<!-- A summary for a report that sends the reader to the dashboard: enough to recognise a clip, and -->
<!-- never the copy or the transcript, which the reader reads in the dashboard. -->
<!-- source names the episode or external video that the clip was cut from. -->
<!-- source_published includes its short publish date in parentheses when known, e.g. (20 May 2026). -->
<!-- A clip can be cut from a source of any age, and the reader judges an old moment differently. -->
<!-- channels lists every channel the clip went to, because a clip is one post on each of them. -->
<!-- The label links to the post of the first channel listed, so post_url is that post's link. -->
<!-- The summary is quoted for the same reason a performance card is: it is the only container -->
<!-- Markdown can make, and every clip in a report is held the same way. -->
<!-- The two lines carry no blank line between them, because a blank line ends a quote and would -->
<!-- give the reader two containers holding half a clip each. -->

> ### [{label}]({post_url})
>
> {source}{source_published} - {channels}
