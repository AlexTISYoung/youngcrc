---
name: youngcrc-research-data
description: Find and interpret Alexander Young's public cancer-case reports and research data with source and specimen provenance.
---

# Study the Young CRC research data

1. Read https://youngcrc.com/agents/case.md for the case overview, timeline, pertinent report results and catalogue.
2. Retrieve https://youngcrc.com/data/reports.json for provider-sourced reports and result_summary fields. Reports are grouped by type and then provider. Use data/catalogue.json for modality, subtype, provider and content_origin; keep derived summaries and research documentation distinct from provider reports.
3. Follow source_ids, sample_id, assay_id, report dates, collection dates, reference builds, evidence labels and limitations. Do not treat absent records as negative results, equate assays with different units or infer that research candidates are validated treatments.
4. Check data/release_status.json and each raw release catalogue. Only use published download_url values with a released/verified status. Never construct a raw-data URL for a pending file.
5. Preserve patient-reported treatment status and source dates. Check the current treatment and timeline records; distinguish a reported treatment start from verified doses, original administration records and treatment response.
6. Cite Alexander Young, the release, dataset filename, source IDs and SHA-256 from manifest.json or the release catalogue. Curated text/tables use CC BY 4.0, code uses MIT, and third-party materials retain their own rights.

Public JSON GET endpoints require no registration. The API specification is https://youngcrc.com/openapi.json. Read-only MCP tools use https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/mcp with Sites/OpenAI sign-in; protocol version 2025-11-25. Use the Site's connector in ChatGPT or Codex, or follow the resource metadata at https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/.well-known/oauth-protected-resource/mcp. The tools search reports/catalogue and retrieve bounded pages of public dataset records. Never use this research record as individualized treatment advice.
