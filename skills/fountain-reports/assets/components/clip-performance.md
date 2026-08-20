<!-- Data: one card per clip - title, learning, and one row for each channel it went to, plus the total. -->
<!-- window names the span these clips cover, e.g. "Last 24 hours", and matches the span you reported. -->
<!-- A row holds platform, published, reactions, eng_rate, views. -->
<!-- platform is written the way the platform writes itself - Instagram, X, YouTube - and links to that -->
<!-- channel's own post, because a clip is one post on each channel and the reader wants the one they read. -->
<!-- One card carries every platform the clip went to, because the reader judges a clip and not a post. -->
<!-- published is the publish time, so the reader can see the hour a result came from. -->
<!-- reactions is likes plus comments. -->
<!-- eng_rate is reactions divided by views. Write "-" when views are zero. -->
<!-- The total row sums the platforms of this clip alone. -->
<!-- learning is what this clip alone teaches. Drop the line when the caller gave none. -->
<!-- The title links to the post in the dashboard, the same way a candidate card does: show_id is the -->
<!-- ContentID of the show, one of ProjectOverview.shows, and post_id is the post of the first row. -->
<!-- A clip holds one post per channel, and the rows below name the rest. -->

## Latest Clips

{window}

### [{title}](https://beta.fountain.fm/studio/{show_id}/posts/{post_id})

| Channel                  | Published   |   Reactions |  Eng. rate |   Views |
| ------------------------ | ----------- | ----------: | ---------: | ------: |
| [{platform}]({post_url}) | {published} | {reactions} | {eng_rate} | {views} |
| **Total**                |             | {reactions} | {eng_rate} | {views} |

{learning}
