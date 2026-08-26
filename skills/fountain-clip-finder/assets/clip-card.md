<!-- The clip card: how a clip is presented in the chat, one card per clip, in rank order. -->
<!-- Chat only - a report presents a clip with the components of skill fountain-reports. -->
<!-- Every value comes from the clip's draft posts, and the card never invents a field. -->
<!-- {episode} is the way the show names it, e.g. #654, and {episode_published} is the day that -->
<!-- episode came out, because the reader judges an old moment differently. -->
<!-- {why} is one or two sentences: the trend or the request the clip answers, and its score. -->
<!-- {transcript} is source.transcript, quoted whole - an ellipsis reads as a cut in the video. -->
<!-- One text line per channel the clip went to, labelled by platform, each from its own post. -->
<!-- Add one line for each flag the clip carries, e.g. an uncertain speaker, because the reader -->
<!-- approves only what they can see. -->
<!-- {post_url} is https://{domain}/studio/{show_id}/posts/{post_id}, the post of the first channel -->
<!-- listed. show_id is the ContentID of the show, one of ProjectOverview.shows, and never the -->
<!-- project id. The domain is beta.fountain.fm while Fountain tests, and fountain.fm in full -->
<!-- production. -->

### {title}

{episode} ({episode_published})

**Why this clip:** {why}

> {transcript}

- **{platform}:** {text}

**[Review this draft]({post_url})**

<!-- After the last card, one link to everything that waits, on the same domain rule: -->
<!-- {drafts_url} is https://{domain}/studio/{show_id}/posts?tab=DRAFT -->

**[Review all drafts]({drafts_url})**
