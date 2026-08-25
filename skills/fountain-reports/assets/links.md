<!-- Every Fountain address a report can hold, each written one time. -->
<!-- A component names the value it needs and never spells an address, so an address that changes -->
<!-- changes here alone. -->

The domain is `beta.fountain.fm` while Fountain tests, and `fountain.fm` in full production.
Change it here, and every report follows.

- `post_url` - a post in the dashboard: `https://{domain}/studio/{show_id}/posts/{post_id}`.
  `show_id` is the ContentID of the show, one of `ProjectOverview.shows`, and never the project id.
  `post_id` is the post of the channel the link is about.
- `drafts_url` - the posts that wait for a decision: `https://{domain}/studio/{show_id}/posts?tab=DRAFT`.
  The DRAFT tab is where a post waits, so the link lands on the work and not on the list.
- `platform_icon` - the mark of a platform:
  `https://storage.googleapis.com/fountain-fm-assets/icons/{instagram|x|youtube}-icon.webp`.
  The mail sizes it, so give the address alone.

The URL structure is the same whether Fountain hosts the show or not.
