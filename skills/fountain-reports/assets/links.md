Below

- `project_id` is `ProjectOverview._id`
- `entity_id` is one of `ProjectOverview.feeds` for hosted feeds and one of `ProjectOverview.shows` for external shows

## `post_url`

- `https://beta.fountain.fm/studio/{project_id}/~/posts/{post_id}` - for posts without a Fountain podcast as source
- `https://beta.fountain.fm/studio/{project_id}/{entity_id}/posts/{post_id}` - for posts with a Fountain podcast as source

## `drafts_url`

- `https://beta.fountain.fm/studio/{project_id}/~/posts?tab=DRAFT` - all draft posts of a project
- `https://beta.fountain.fm/studio/{project_id}/{entity_id}/posts?tab=DRAFT` - project drafts posts scoped to a Fountain podcast

## `platform_icon`

- `https://storage.googleapis.com/fountain-fm-assets/icons/{instagram|x|youtube}-icon.webp`
