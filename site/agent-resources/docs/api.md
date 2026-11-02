# Young CRC public data API

Canonical origin: https://youngcrc.com. Release 1.53. All operations are read-only. Public JSON files need no authentication. GET returns the complete document; it does not accept server-side filters. Schema and paths: [OpenAPI](https://youngcrc.com/openapi.json).

## Start here

- Reports and pertinent findings: `/data/reports.json` (`records` array).
- Dataset metadata by modality, subtype and provider: `/data/catalogue.json` (`records` array).
- Clinical timeline: `/data/clinical/timeline.json` (array).
- Molecular evidence: `/data/molecular/findings.json` (`records` array).
- Treatment plans/evidence: `/data/clinical/treatment_options.json`.
- Availability: `/data/release_status.json`; this describes data preparation, not server health.
- File sizes and checksums: `/manifest.json`, `/checksums.sha256`, `/external-checksums.sha256`.

`GET /` or `/index.html` with `Accept: text/markdown` returns a generated Markdown case view. Browsers receive HTML by default. `/agents/case.md` and `/llms.txt` are directly readable.

## GitHub companion repository

The [GitHub repository](https://github.com/AlexTISYoung/youngcrc) provides a versioned public snapshot, agent instructions and tools for data access, checksum verification and local analysis. Read its README and AGENTS.md before analysis. Use the website manifest and catalogues to check the latest release and large-file availability.

## Read-only MCP

Endpoint: https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/mcp. MCP requires Sites/OpenAI sign-in; use the Site's connector in ChatGPT or Codex. Authentication and client registration: [auth.md](https://youngcrc.com/auth.md). Public JSON remains available without sign-in.

After authorization, POST with `Content-Type: application/json` and `Accept: application/json, text/event-stream`. Supports MCP 2025-11-25 initialization, `tools/list` and `tools/call`, with JSON responses and no server-to-client stream. Subsequent requests include `MCP-Protocol-Version: 2025-11-25`. Tools: `search_reports`, `search_catalogue`, `get_public_dataset`. Arrays and `records` documents return bounded pages, a total count, the full public URL and any document-level metadata; use offset/limit for all records. Large documents with another schema return their public URL for direct retrieval. No session ID is required. Authorized GET requests return 405. Tool definitions contain exact input schemas.

## Interpretation and reuse

Keep source/sample/assay IDs, dates, units, reference genomes, evidence labels and limitations with findings. Missing data are not negative findings. Treatment plans are not records of administered care. Use only verified published download URLs; do not generate URLs for pending files. Cite Alexander Young, the release, dataset filename and SHA-256. My text/tables use CC BY 4.0; code uses MIT. Third-party materials retain their own rights. Search, agent input and model training are allowed for my content.
