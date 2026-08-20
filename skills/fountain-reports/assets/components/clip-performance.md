<!-- Data: one card per clip - title, learning, and one row for each channel it went to, plus the total. -->
<!-- A row holds platform, published, reactions, eng_rate, views. -->
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

### [{title}](https://beta.fountain.fm/studio/{show_id}/posts/{post_id})

| Channel    | Published   |   Reactions |  Eng. rate |   Views |
| ---------- | ----------- | ----------: | ---------: | ------: |
| {platform} | {published} | {reactions} | {eng_rate} | {views} |
| **Total**  |             | {reactions} | {eng_rate} | {views} |

{learning}
