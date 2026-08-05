---
name: fountain-api
description: Interact with the Fountain API. Load and search content, publish your own podcasts, create social posts.
---

## Overview

The Fountain API is fully defined at https://fountain.fm/docs.md.
The docs are the ONLY source of truth.

## Input

Freeform input that targets one or more parts of the Fountain API.

## Output

Fountain API responses.

## Housekeeping

You MUST read HOUSEKEEPING.md if you haven't already.

## Requirements

- An HTTP client, e.g. curl.

## Process

1. Read https://fountain.fm/docs.md in each new session.
   This page is an index.
   Read the pages that it links to for the parts of the API that you need.
   When a skill names a model, read the page of that model before you use it.
2. Find the project API key in the `FOUNTAIN_API_KEY` environment variable or in `.env`.
3. Send each request with `FOUNTAIN_API_KEY` as a bearer token in the `Authorization` header.

## Additional notes

You MUST read https://fountain.fm/docs.md in each new session.
The API can change.

You CAN write a throwaway script, e.g. to do the same request for many items.
You CAN write a response to a file, e.g. to give a large transcript to a script.
You MUST put each in a temporary location and delete it at the end of the session.
You MUST NOT keep a script that wraps the Fountain API, because the API can change.

If there is no `FOUNTAIN_API_KEY`:

- Ask the user to create a project API key at https://fountain.fm/studio/api.
- Ask the user to copy the agent instructions from that page and to paste them to you.
  These instructions give you a safe way to store the key - a one-time link that you pipe into `.env`.

If a request fails with an authentication error, make sure that the key starts with `fountain_`.
If the prefix is different, the key can be for a different service, and you MUST tell the user.

You MUST NOT write the key into logs, command output, or files other than the key store.
If the key store is `.env`, you MUST make sure that `.gitignore` contains `.env`.
