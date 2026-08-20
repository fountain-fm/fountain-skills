<!-- Data: one row per platform - platform, posts, reactions, eng_rate, views. -->
<!-- This is what each platform did in the window, and never a baseline. -->
<!-- posts is how many published posts the row counts. -->
<!-- reactions is likes plus comments. -->
<!-- eng_rate is reactions divided by views. Write "-" when views are zero. -->
<!-- The total row sums the platforms, and every table in a report ends on one, so a reader and a -->
<!-- stylesheet can both take the last row to be the total. -->
<!-- counted says what the table covers: the days, the posts in them, and how many are published. -->
<!-- The clips below cover a shorter span, so without this line a reader takes these totals for it. -->

## Channels Overview

| Platform   |   Posts |   Reactions |  Eng. rate |   Views |
| ---------- | ------: | ----------: | ---------: | ------: |
| {platform} | {posts} | {reactions} | {eng_rate} | {views} |
| **Total**  | {posts} | {reactions} | {eng_rate} | {views} |

{counted}
