<!-- Data: one card per clip - title and one row for each channel it went to, plus the total. -->
<!-- window names the span these clips cover, e.g. "Last 24 hours", and matches the span you reported. -->
<!-- A row holds platform, published, reactions, eng_rate, views. -->
<!-- platform is written the way the platform writes itself - Instagram, X, YouTube - and links to that -->
<!-- channel's own post, because a clip is one post on each channel and the reader wants the one they read. -->
<!-- Its mark comes from the Fountain assets, named for the platform: -->
<!-- https://storage.googleapis.com/fountain-fm-assets/icons/{instagram|x|youtube}-icon.webp -->
<!-- One card carries every platform the clip went to, because the reader judges a clip and not a post. -->
<!-- published is the publish time, so the reader can see the hour a result came from. -->
<!-- episode names the episode the clip was cut from, and episode_published the day it came out, e.g. -->
<!-- 20 May 2026, because a number reads differently against a clip cut from an old episode. -->
<!-- reactions is likes plus comments. -->
<!-- eng_rate is reactions divided by views. Write "-" when views are zero. -->
<!-- The total row sums the platforms of this clip alone. -->
<!-- The card is a quote because that is the only container Markdown can make: no div survives the -->
<!-- sender, so a clip's title, its episode and its figures are held together by being quoted. -->
<!-- The title links to the post in the dashboard, the same way a candidate card does: show_id is the -->
<!-- ContentID of the show, one of ProjectOverview.shows, and post_id is the post of the first row. -->
<!-- A clip holds one post per channel, and the rows below name the rest. -->
<!-- The window is written as emphasis, which is the only mark that separates it from an ordinary -->
<!-- paragraph under a heading. The mail stylesheet draws it as a label, and not as italics. -->

## Latest Clips

_{window}_

> ### [{title}](https://beta.fountain.fm/studio/{show_id}/posts/{post_id})
>
> {episode} ({episode_published})
>
> | Channel                                                 | Published   |   Reactions |  Eng. rate |   Views |
> | ------------------------------------------------------- | ----------- | ----------: | ---------: | ------: |
> | [![{platform}]({platform_icon}) {platform}]({post_url}) | {published} | {reactions} | {eng_rate} | {views} |
> | **Total**                                               |             | {reactions} | {eng_rate} | {views} |
