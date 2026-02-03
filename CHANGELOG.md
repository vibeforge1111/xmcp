# XMCP Update Log

This project is based on the upstream MIT-licensed server:
`https://github.com/rafaljanicki/x-twitter-mcp-server`

## 2026-02-03

Enhancements added in XMCP:

- Expanded tool surface (70+ tools) across research, engagement, publishing, social, lists, DMs
- Permission profiles and tool grouping, plus runtime permission enforcement
- Playwright-powered article fetching for X articles (JS-rendered content)
- HTTP server mode with CORS and Smithery per-request config middleware
- Standardized error envelope and improved rate-limit signaling
- Human-in-the-loop advisory for publishing tools
- Safer client initialization and pagination fixes (e.g., bookmark deletion)
- Broader client compatibility configs and agent rules
- Basic test coverage for permission refresh and error handling
