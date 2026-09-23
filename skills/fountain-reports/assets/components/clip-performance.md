<!-- Data: one card per clip - label, post_url, platform_icon, and one row for each channel, plus the total. -->
<!-- window names the span these clips cover, e.g. "Last 24 hours", and matches the span you reported. -->
<!-- A row holds platform, published, reactions, eng_rate, views. -->
<!-- platform is written the way the platform writes its own name - Instagram, X, YouTube. -->
<!-- platform links to that channel's own post. -->
<!-- A clip is one post on each channel, and the reader wants the post that they read. -->
<!-- One card holds every platform the clip went to, because the reader judges a clip and not a post. -->
<!-- published is the publish time, so the reader can see the hour a result came from. -->
<!-- source names the episode or external video that the clip was cut from. -->
<!-- source_published includes its date in parentheses when known, e.g. (20 May 2026). -->
<!-- The reader judges a number differently for a clip cut from an old source. -->
<!-- reactions is likes plus comments. -->
<!-- eng_rate is reactions divided by views. Write "-" when views are zero. -->
<!-- The total row sums the platforms of this clip alone. -->
<!-- The card is a quote, because a quote is the only container that Markdown can make. -->
<!-- The sender removes every div. -->
<!-- So the quote is what holds a clip's label, its episode and its figures together. -->
<!-- The label links to the post of the first row, and each row to the post of its own channel. -->
<!-- A clip holds one post per channel, and the rows below name the rest. -->
<!-- The window is written as emphasis, which is the only mark that separates it from an ordinary -->
<!-- paragraph under a heading. The mail shows it as a label, and not as italics. -->

## Latest Clips

_{window}_

> ### [{label}]({post_url})
>
> {source}{source_published}
>
> | Channel                                                | Published   |   Reactions |  Eng. rate |   Views |
> | ------------------------------------------------------ | ----------- | ----------: | ---------: | ------: |
> | [![{platform}]({platform_icon}){platform}]({post_url}) | {published} | {reactions} | {eng_rate} | {views} |
> | **Total**                                              |             | {reactions} | {eng_rate} | {views} |
