<!-- Data: one row per platform - platform, posts, reactions, eng_rate, views. -->
<!-- This is what each platform did in the window, and never a baseline. -->
<!-- posts is how many published posts the row counts. -->
<!-- platform carries its mark, from the Fountain assets and named for the platform: -->
<!-- https://storage.googleapis.com/fountain-fm-assets/icons/{instagram|x|youtube}-icon.webp -->
<!-- reactions is likes plus comments. -->
<!-- eng_rate is reactions divided by views. Write "-" when views are zero. -->
<!-- The total row sums the platforms, and every table in a report ends on one, so a reader and a -->
<!-- stylesheet can both take the last row to be the total. -->
<!-- window names the span these totals cover, e.g. "Last 7 days". It sits under the heading because -->
<!-- the clips below cover a shorter one, and a reader who cannot see both spans reads the wrong number. -->

## Channels Overview

{window}

| Platform                                  |   Posts |   Reactions |  Eng. rate |   Views |
| ----------------------------------------- | ------: | ----------: | ---------: | ------: |
| ![{platform}]({platform_icon}) {platform} | {posts} | {reactions} | {eng_rate} | {views} |
| **Total**                                 | {posts} | {reactions} | {eng_rate} | {views} |
