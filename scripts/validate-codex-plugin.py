#!/usr/bin/env python3
"""Validate the Codex plugin manifest and its inline MCP server map."""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"


def fail(message: str) -> None:
    print(f"validate-codex-plugin: {message}", file=sys.stderr)
    raise SystemExit(1)


try:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    fail(f"cannot read {MANIFEST_PATH}: {error}")

mcp_servers = manifest.get("mcpServers")
if not isinstance(mcp_servers, dict) or not mcp_servers:
    fail("mcpServers must be a non-empty inline server map")

if "mcpServers" in mcp_servers or "mcp_servers" in mcp_servers:
    fail("mcpServers must contain servers directly, without a wrapper")

for server_name, server in mcp_servers.items():
    if not isinstance(server_name, str) or not server_name:
        fail("each MCP server must have a non-empty name")
    if not isinstance(server, dict):
        fail(f"MCP server {server_name!r} must be an object")
    if server.get("type") != "http":
        fail(f"MCP server {server_name!r} must use the http type")

    server_url = server.get("url")
    if not isinstance(server_url, str):
        fail(f"MCP server {server_name!r} must have a URL")

    parsed_url = urlparse(server_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        fail(f"MCP server {server_name!r} must use an absolute HTTPS URL")

print("Codex plugin manifest is valid")
