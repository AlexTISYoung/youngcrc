# Young CRC authentication

## Public data

Read https://youngcrc.com/agents/case.md and download JSON, reports and data with HTTPS GET. No account, credentials or agent registration are required.

## MCP tools and client registration

The read-only MCP endpoint is https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/mcp. Use the Site's connector in ChatGPT or Codex; Sites/OpenAI manages client configuration and user sign-in. This application does not provide separate agent registration, claim or revocation endpoints.

Unauthenticated MCP requests return HTTP 401 with a `WWW-Authenticate` link to [protected resource metadata](https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/.well-known/oauth-protected-resource/mcp). The resource identifier is the MCP endpoint above. Its authorization server is https://auth.openai.com; [OpenID discovery](https://auth.openai.com/.well-known/openid-configuration) describes its authorization-code flow with PKCE S256. The required scopes reported by the MCP challenge are `openid resource.invoke email`. Request tokens for the exact resource identifier and send them only to that endpoint.

All tools are read-only. For clients without supported Sites authentication, use the public JSON API directly. Never send credentials to public dataset or download URLs.
