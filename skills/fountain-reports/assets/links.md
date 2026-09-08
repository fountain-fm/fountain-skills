<!-- Every Fountain address a report can hold, each written one time. -->
<!-- A component names the value it needs and never spells an address, so an address that changes -->
<!-- changes here alone. -->

Fountain is in test, so the domain of every reader-facing link is `beta.fountain.fm`.
It becomes `fountain.fm` in full production.
Change it here, and every report follows.

Every dashboard address starts `https://{domain}/studio/{project_id}/{entity_id}`.
`project_id` is `ProjectOverview._id`.
`entity_id` names the show: its feed id when the project hosts it, one of `ProjectOverview.feeds`,
and its ContentID when the project does not, one of `ProjectOverview.shows`.
A show that is in both is hosted, so the feed id wins and the reader lands on one page and not two.

- `post_url` - a post in the dashboard:
  `https://{domain}/studio/{project_id}/{entity_id}/posts/{post_id}`.
  `post_id` is the post of the channel the link is about.
- `drafts_url` - the posts that wait for a decision:
  `https://{domain}/studio/{project_id}/{entity_id}/posts?tab=DRAFT`.
  The DRAFT tab is where a post waits, so the link lands on the work and not on the list.
- `platform_icon` - the mark of a platform:
  `https://storage.googleapis.com/fountain-fm-assets/icons/{instagram|x|youtube}-icon.webp`.
  The mail sizes it, so give the address alone.
