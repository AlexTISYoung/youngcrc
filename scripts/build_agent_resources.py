#!/usr/bin/env python3
"""Generate discovery documents from the same reviewed sources as the website."""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site' / 'agent-resources'
ORIGIN = 'https://youngcrc.com'
REPO_URL = 'https://github.com/AlexTISYoung/youngcrc'
# Verified by Sites get_site(include_mcp_connection=True); custom domains do not route MCP.
MCP_URL = 'https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/mcp'
MCP_METADATA_URL = 'https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/.well-known/oauth-protected-resource/mcp'
RELEASE = '1.53'

def read(path):
    return json.loads((ROOT / path).read_text())

def rows(doc):
    return doc if isinstance(doc, list) else doc.get('records', [])

def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False) + '\n')

def url(path):
    return ORIGIN + '/' + path.lstrip('/')

def text(value):
    if value is None:
        return 'Not recorded'
    if isinstance(value, list):
        return '; '.join(text(x) for x in value)
    if isinstance(value, dict):
        return '; '.join(k.replace('_', ' ') + ': ' + text(v) for k, v in value.items())
    return str(value)

class PageText(HTMLParser):
    """Readable source copy; dynamic records are appended directly from JSON."""
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
        self.anchors = []
    def handle_starttag(self, tag, attrs):
        if tag in {'head', 'script', 'style', 'nav', 'header', 'footer', 'noscript', 'button', 'label', 'select'}:
            self.skip += 1
        if not self.skip:
            if tag in {'p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'h4'}:
                self.parts.append('\n\n')
            if tag in {'h1', 'h2', 'h3', 'h4'}:
                self.parts.append('#' * int(tag[1]) + ' ')
            if tag == 'a':
                href = dict(attrs).get('href', '')
                self.anchors.append(href if href.startswith('https://') else url(href))
                self.parts.append('[')
    def handle_endtag(self, tag):
        if not self.skip and tag == 'a' and self.anchors:
            self.parts.append('](' + self.anchors.pop() + ')')
        if not self.skip and tag in {'h1', 'h2', 'h3', 'h4'}:
            self.parts.append('\n\n')
        if tag in {'head', 'script', 'style', 'nav', 'header', 'footer', 'noscript', 'button', 'label', 'select'}:
            self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data + ' ')

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = rows(read('data/reports.json'))
    catalogue = rows(read('data/catalogue.json'))
    timeline = rows(read('data/clinical/timeline.json'))
    providers = {r['provider_id']: r['name'] for r in rows(read('data/providers.json'))}
    page = PageText()
    source_page = (ROOT / 'site/index.html').read_text()
    source_page = re.sub(r'<div id="load-error".*?</div>', '', source_page, flags=re.S)
    source_page = re.sub(r'<a class="skip".*?</a>', '', source_page, flags=re.S)
    page.feed(source_page)
    copy = re.sub(r'\n\s*\n(?:\s*\n)+', '\n\n', ''.join(page.parts)).strip()
    copy = '\n'.join(line.rstrip() for line in copy.splitlines())
    md = [f'# Alexander Young: early onset metastatic rectal cancer case\n\nCanonical website: {ORIGIN}/\n\nRelease {RELEASE} · 29 October 2026.\n\nThis Markdown view includes source-page text and the records loaded by the website. Full records and provenance remain in the linked JSON.\n\n', copy]
    md += ['\n\n## Clinical timeline\n']
    for r in timeline:
        md += [f"\n### {r.get('date') or r.get('start_date') or 'Date unconfirmed'} — {r.get('title', 'Clinical event')}\n\n{r.get('summary', '')}\n\nEvidence: {text(r.get('evidence_status') or r.get('evidence_type') or r.get('status') or r.get('date_basis'))}. Sources: {text(r.get('source_ids'))}.\n"]
    context = read('data/clinical/dataset_info.json').get('patient_reported_context', {})
    treatments = read('data/clinical/treatment_options.json')
    md += [f'\n## My reported context and current treatment\n\nI was {context.get("age_at_diagnosis")} when diagnosed and am now {context.get("current_age")}. I have had no prior anti-VEGF treatment (reported {context.get("prior_anti_VEGF_reported_on")}). I report starting {text(context.get("current_systemic_regimen"))} on {context.get("systemic_treatment_start_date")}; reported {context.get("reported_on")}. Sources: {text(context.get("source_ids"))}. Doses and schedule are not recorded here.\n']
    for plan in treatments.get('plans', []):
        md += [f'\n### {plan.get("title")}\n\nStatus: {plan.get("status_label")}.\n\n{plan.get("body", "")}\n']
        for key in ['rationale', 'evidence_summary', 'timing', 'evidence_needed', 'public_caveat']:
            if plan.get(key):
                md += [f'\n{key.replace("_", " ").capitalize()}: {text(plan[key])}\n']
        for link in plan.get('links', []):
            if link.get('url'):
                md += [f'\nSource: [{link.get("label", "Reference")}]({link["url"]})\n']
    md += ['\n## Potential therapeutics and trials\n']
    shortlist = treatments['shortlist']
    for r in shortlist['drug_rows'] + shortlist['cell_rows']:
        md += [f'\n### {r["candidate"]}\n\n{r["mechanism"]}. Evidence: {r["evidence_type"]}. Reviewed: {r.get("reviewed_on", shortlist["reviewed_on"])}.\n\n{r["evidence"]}\n\nAccess: {r["access"]}\n\nLimitation: {r["caveat"]}\n']
        for link in r.get('sources', []):
            target = link['url']
            md += [f'\nSource: [{link["label"]}]({target if target.startswith("https://") else url(target)})\n']
    research = treatments.get('immune_evasion_research')
    if research:
        md += [f'\n## {research["title"]}\n\n{research["summary"]}\n']
        for link in research['links']:
            target = link['url']
            md += [f'\n[{link["label"]}]({target if target.startswith("https://") else url(target)})\n']
    combination = treatments.get('combination_immunotherapy')
    if combination:
        md += [f'\n## {combination["title"]}\n\n{combination["intro"]}\n']
        for option in combination['options']:
            md += [f'\n### {option["name"]}\n\nPotential contribution: {option["role"]}\n\nEvidence / main limitation: {option["limitation"]}\n']
            for link in option['sources']:
                md += [f'\n[{link["label"]}]({link["url"]})\n']
        md += [f'\n{combination["combination_note"]}\n']
    md += [f'\nFull timeline: {url("data/clinical/timeline.json")}\n\n## Reports: pertinent results\n']
    for r in sorted(reports, key=lambda r: (r.get('browse_type', ''), r.get('provider_id', ''), r.get('title', ''))):
        md += [f"\n### {r.get('title', r.get('report_id', 'Report'))}\n\nType: {r.get('browse_type', 'See record')}. Provider: {providers.get(r.get('provider_id'), r.get('provider_id', 'See record'))}.\n\n{r.get('description', '')}\n"]
        summary = r.get('result_summary') or {}
        for finding in summary.get('findings', []):
            md += ['\n- ' + text(finding)]
        if summary.get('note'):
            md += ['\n\n' + summary['note']]
        for key in ['basis', 'pages', 'section']:
            if summary.get(key):
                md += [f'\n\nSummary {key}: {text(summary[key])}']
        for k in ['report_id', 'collection_date', 'report_date', 'evidence_class', 'specimens', 'assay_ids', 'provenance_summary', 'source_ids', 'limitations']:
            if r.get(k):
                md += [f'\n\n{k.replace("_", " ").capitalize()}: {text(r[k])}']
        target = r.get('download_url') or r.get('path')
        if target:
            md += [f'\n\nReport: {target if target.startswith("https://") else url(target)}\n']
    md += [f'\nFull report metadata: {url("data/reports.json")}\n\n## Molecular evidence\n']
    for r in rows(read('data/molecular/findings.json')):
        md += ['\n```json\n' + json.dumps(r, indent=2, ensure_ascii=False) + '\n```\n']
    summary = read('data/molecular/summary.json')
    md += ['\n## My molecular profile and vaccine targets\n\n' + summary['context_note'] + '\n']
    for category in summary['variant_groups']:
        md += ['\n### ' + category['title'] + '\n\n' + category['note'] + '\n']
        for r in category['records']:
            md += ['\n#### ' + r['variant'] + '\n\n' + (r.get('dna_change') or '') + '\n\n' + '\n\n'.join(r['evidence_lines']) + '\n\n' + r['therapy_connection'] + '\n']
            if r.get('note'):
                md += ['\n' + r['note'] + '\n']
            for source in r['sources']:
                target = source['url']
                md += [f'\nSource: {target if target.startswith("https://") else url(target)}; IDs: {text(source.get("source_ids"))}; specimen: {source.get("sample_id", "See source")}; assay: {source.get("assay_id", "See source")}; audit records: {text(source.get("record_ids"))}.\n']
            for link in r.get('therapy_links', []):
                target = link['url']
                md += [f'\nTherapy evidence: [{link["label"]}]({target if target.startswith("https://") else url(target)})\n']
    md += ['\n### Treatment and immune biomarkers\n']
    for r in summary['biomarker_rows']:
        md += [f'\n#### {r["biomarker"]}\n\n{r["summary"]}\n\n{r["therapy_connection"]}\n']
        for source in r.get('sources', []):
            target = source.get('url')
            if target:
                md += [f'\nSource: {target if target.startswith("https://") else url(target)}; IDs: {text(source.get("source_ids"))}; records: {text(source.get("record_ids"))}.\n']
    md += ['\n### Expression and pathology\n\n' + summary['expression_note'] + '\n\n' + summary['specimen_note'] + '\n']
    for r in summary['expression_rows']:
        md += [f'\n#### {r["target"]}\n\nRNA: {r["rna_summary"]}\n\nProtein: {r["protein_summary"]}\n\n{r["therapy_connection"]}\n']
        for source in r['sources']:
            md += [f'\nSource: {source["url"]}; IDs: {text(source.get("source_ids"))}.\n']
    if summary.get('caris_blood_rna_context'):
        md += ['\n#### Caris Assure blood RNA\n\n' + summary['caris_blood_rna_context'] + '\n']
        for source in summary['caris_blood_rna_sources']:
            md += [f'\nSource: {url(source["url"])}; IDs: {text(source.get("source_ids"))}; records: {text(source.get("record_ids"))}.\n']
    md += ['\n' + summary['bostongene_immunecontext'] + '\n\n' + summary['pathology'] + '\n\n### JLF and Invoke vaccine targets\n\n' + summary['vaccine']['introduction_first_person'] + '\n\n' + summary['vaccine']['summary'] + '\n\nInvoke allele fractions and TPM are maxima across available samples; they are not a single specimen’s unified measurements. HLA restrictions below come from JLF designs; Invoke supplies no candidate-specific HLA allele columns.\n\n| Target | JLF HLA / class I core | Invoke tier / rank | RNA AF / TPM | Invoke peptide |\n|---|---|---|---|---|\n']
    vaccine_rows = summary['vaccine']['records'] + [{'gene': r['gene'], 'protein_change': r['protein_change'], 'invoke': r} for r in summary['vaccine']['remaining_invoke_rows']]
    for r in vaccine_rows:
        inv = r['invoke']
        jlf = r.get('jlf')
        restriction = f'{jlf["hla_restriction"]} / {jlf["class_i_epitope"]}' if jlf else 'Not in JLF list'
        md += [f'| {r["gene"]} {r["protein_change"]} | {restriction} | {inv["tier"]} / {inv["rank"]} | {inv["rna_af_display"]} / {inv["rna_tpm_display"]} | {inv["full_peptide"]} |\n']
    for r in summary['vaccine']['records']:
        if r.get('sequence_notes') or r.get('research_audits') or r.get('jlf'):
            md += [f'\n#### Vaccine sequence evidence: {r["gene"]} {r["protein_change"]}\n']
            if r.get('jlf'):
                md += [f'\nJLF precursor: {r["jlf"]["full_precursor"]}. Class I: {r["jlf"]["class_i_epitope"]}. Class II: {r["jlf"].get("class_ii_epitope") or "Not specified"}.\n']
            md += ['\n' + '\n\n'.join(r.get('sequence_notes', [])) + '\n']
            for audit in r.get('research_audits', []):
                md += [f'\n{audit["evidence_id"]}: {audit["summary"]} {audit["assessment"]}\n']
    md += [f'\nFull source-linked molecular summary: {url("data/molecular/summary.json")}\n\nJLF source: {url("reports/jlf/peptide_candidate_list.html")}\n\nInvoke source: {url("reports/invoke/aureon_vaccine_target_report.html")}\n']
    md += [f'\nMolecular evidence: {url("data/molecular/findings.json")}\n\n## Data catalogue\n']
    for r in sorted(catalogue, key=lambda r: (r.get('browse_modality', ''), r.get('browse_type', ''), r.get('provider_id', ''))):
        target = r.get('download_url') or r.get('path')
        md += [f"\n### {r.get('title', 'Dataset')}\n\nModality: {r.get('browse_modality')}. Type: {r.get('browse_type')}. Provider: {providers.get(r.get('provider_id'), r.get('provider_id'))}. Origin: {r.get('content_origin', 'See full record')}.\n\n{r.get('description', '')}\n"]
        if target:
            md += ['\nDownload: ' + (target if target.startswith('https://') else url(target)) + '\n']
    md += [f'\n## Full structured records\n\nTreatment plans and evidence: {url("data/clinical/treatment_options.json")}\n\nLaboratory measurements: {url("data/clinical/laboratory_observations.json")}\n\nClinical source metadata: {url("data/clinical/sources.json")}\n\nNative sequencing: {url("data/molecular/raw_release_catalog.json")}\n\nNative imaging: {url("data/imaging_release_catalog.json")}\n\nNative pathology: {url("data/pathology_release_catalog.json")}\n\nAvailability and gaps: {url("data/release_status.json")} and {url("data/gaps.json")}\n\nChecksums: {url("manifest.json")} and {url("checksums.sha256")}\n']
    write('agents/case.md', ''.join(md))
    skill = f'''---
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
7. For a local checkout, use {REPO_URL}. Read its AGENTS.md and README before analysis; it includes a versioned public snapshot and tools for data access and checksum verification. Check the website manifest for later releases.

Public JSON GET endpoints require no registration. The API specification is https://youngcrc.com/openapi.json. Read-only MCP tools use {MCP_URL} with Sites/OpenAI sign-in; protocol version 2025-11-25. Use the Site's connector in ChatGPT or Codex, or follow the resource metadata at {MCP_METADATA_URL}. The tools search reports/catalogue and retrieve bounded pages of public dataset records. Never use this research record as individualized treatment advice.
'''
    write('.well-known/agent-skills/youngcrc-research-data/SKILL.md', skill)
    write('.well-known/agent-skills/index.json', {'$schema': 'https://schemas.agentskills.io/discovery/0.2.0/schema.json', 'skills': [{'name': 'youngcrc-research-data', 'type': 'skill-md', 'description': "Find and interpret Alexander Young's public cancer-case reports and research data with source and specimen provenance.", 'url': url('.well-known/agent-skills/youngcrc-research-data/SKILL.md'), 'digest': 'sha256:' + hashlib.sha256(skill.encode()).hexdigest()}]})
    write('robots.txt', '\n'.join('User-agent: ' + x for x in ['*', 'OAI-SearchBot', 'Claude-SearchBot', 'PerplexityBot', 'GPTBot', 'ClaudeBot', 'Google-Extended', 'Applebot-Extended', 'CCBot', 'Bytespider', 'Amazonbot', 'ChatGPT-User', 'Claude-User', 'Perplexity-User']) + '\nAllow: /\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\n\n# Permission applies to my own content; third-party rights remain unchanged.\nSitemap: https://youngcrc.com/sitemap.xml\n')
    sitemap_paths = ['', 'agents/case.md', 'docs/api.md', '.well-known/agent-skills/youngcrc-research-data/SKILL.md']
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{html.escape(url(p))}</loc><lastmod>2026-10-29</lastmod></url>\n' for p in sitemap_paths) + '</urlset>\n')
    write('llms.txt', f'''# Alexander Young: early onset metastatic rectal cancer case

> A patient-led public research record, with provider reports, pertinent findings, treatment history and sequencing, pathology and imaging data.

- [Case and report summaries]({url('agents/case.md')})
- [API documentation]({url('docs/api.md')})
- [OpenAPI]({url('openapi.json')})
- [Research skill]({url('.well-known/agent-skills/youngcrc-research-data/SKILL.md')})
- [Data catalogue]({url('data/catalogue.json')})
- [Reports]({url('data/reports.json')})
- [Timeline]({url('data/clinical/timeline.json')})
- [Release availability]({url('data/release_status.json')})
- [Manifest and checksums]({url('manifest.json')})
- [MCP server card]({url('mcp/server-card')})
- [GitHub companion repository: public snapshot and agent tools]({REPO_URL})

Research use; preserve evidence labels, specimen/source linkage, limitations and third-party rights. No registration is needed to download public data. Pending files have no public download URL.
''')
    write('auth.md', f'''# Young CRC authentication

## Public data

Read https://youngcrc.com/agents/case.md and download JSON, reports and data with HTTPS GET. No account, credentials or agent registration are required.

## MCP tools and client registration

The read-only MCP endpoint is {MCP_URL}. Use the Site's connector in ChatGPT or Codex; Sites/OpenAI manages client configuration and user sign-in. This application does not provide separate agent registration, claim or revocation endpoints.

Unauthenticated MCP requests return HTTP 401 with a `WWW-Authenticate` link to [protected resource metadata]({MCP_METADATA_URL}). The resource identifier is the MCP endpoint above. Its authorization server is https://auth.openai.com; [OpenID discovery](https://auth.openai.com/.well-known/openid-configuration) describes its authorization-code flow with PKCE S256. The required scopes reported by the MCP challenge are `openid resource.invoke email`. Request tokens for the exact resource identifier and send them only to that endpoint.

All tools are read-only. For clients without supported Sites authentication, use the public JSON API directly. Never send credentials to public dataset or download URLs.
''')
    paths = sorted('/' + str(p.relative_to(ROOT)) for p in (ROOT / 'data').rglob('*.json')) + ['/manifest.json']
    write('agents/datasets.json', {'paths': sorted(p for p in paths if p.startswith('/data/'))})
    api = {'openapi': '3.1.0', 'info': {'title': 'Young CRC public research data', 'version': RELEASE, 'description': 'Read-only public dataset files. Clinical, research-derived and patient-reported evidence remain distinct.'}, 'servers': [{'url': ORIGIN}], 'security': [], 'paths': {p: {'get': {'operationId': re.sub('[^a-zA-Z0-9]', '_', p).strip('_'), 'summary': 'Read ' + p, 'responses': {'200': {'description': 'Full released document; individual records retain provenance and limitations.', 'content': {'application/json': {'schema': {}}}}}}} for p in paths}}
    write('openapi.json', api)
    write('docs/api.md', f'''# Young CRC public data API

Canonical origin: {ORIGIN}. Release {RELEASE}. All operations are read-only. Public JSON files need no authentication. GET returns the complete document; it does not accept server-side filters. Schema and paths: [OpenAPI]({url('openapi.json')}).

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

The [GitHub repository]({REPO_URL}) provides a versioned public snapshot, agent instructions and tools for data access, checksum verification and local analysis. Read its README and AGENTS.md before analysis. Use the website manifest and catalogues to check the latest release and large-file availability.

## Read-only MCP

Endpoint: {MCP_URL}. MCP requires Sites/OpenAI sign-in; use the Site's connector in ChatGPT or Codex. Authentication and client registration: [auth.md]({url('auth.md')}). Public JSON remains available without sign-in.

After authorization, POST with `Content-Type: application/json` and `Accept: application/json, text/event-stream`. Supports MCP 2025-11-25 initialization, `tools/list` and `tools/call`, with JSON responses and no server-to-client stream. Subsequent requests include `MCP-Protocol-Version: 2025-11-25`. Tools: `search_reports`, `search_catalogue`, `get_public_dataset`. Arrays and `records` documents return bounded pages, a total count, the full public URL and any document-level metadata; use offset/limit for all records. Large documents with another schema return their public URL for direct retrieval. No session ID is required. Authorized GET requests return 405. Tool definitions contain exact input schemas.

## Interpretation and reuse

Keep source/sample/assay IDs, dates, units, reference genomes, evidence labels and limitations with findings. Missing data are not negative findings. Treatment plans are not records of administered care. Use only verified published download URLs; do not generate URLs for pending files. Cite Alexander Young, the release, dataset filename and SHA-256. My text/tables use CC BY 4.0; code uses MIT. Third-party materials retain their own rights. Search, agent input and model training are allowed for my content.
''')
    write('.well-known/api-catalog', {'linkset': [{'anchor': url('data/reports.json'), 'service-desc': [{'href': url('openapi.json'), 'type': 'application/json'}], 'service-doc': [{'href': url('docs/api.md'), 'type': 'text/markdown'}, {'href': REPO_URL, 'type': 'text/html'}], 'status': [{'href': url('data/release_status.json'), 'type': 'application/json'}]}]})
    entries = []
    for name, display, path, media, queries in [
        ('reports', 'Provider reports and pertinent results', 'data/reports.json', 'application/json', ['What pertinent results does each report contain?', 'Which provider report supports a molecular finding?']),
        ('timeline', 'Clinical timeline', 'data/clinical/timeline.json', 'application/json', ['What treatment has Alexander Young received?', 'Which clinical events are documented versus patient-reported?']),
        ('catalogue', 'Data by modality and provider', 'data/catalogue.json', 'application/json', ['Which sequencing, imaging and pathology data are public?', 'Which files are derived summaries versus provider-sourced data?']),
        ('case', 'Readable case and report summaries', 'agents/case.md', 'text/markdown', ['Summarize the cancer-case evidence with its limitations.', 'What data remain missing or pending?']),
        ('research-skill', 'Research data instructions', '.well-known/agent-skills/youngcrc-research-data/SKILL.md', 'text/markdown', ['How do I study this case with correct source attribution?', 'How do I verify public file availability and checksums?']),
        ('mcp-card', 'Read-only research MCP server', 'mcp/server-card', 'application/mcp-server-card+json', ['Find public reports with read-only agent tools.', 'Retrieve source-linked case data using MCP.']),
        ('github', 'GitHub public snapshot and agent tools', REPO_URL, 'text/html', ['How do I access and verify the public data in a local checkout?', 'Where are the agent instructions and analysis tools?'])]:
        entries.append({'identifier': f'urn:air:youngcrc.com:research:{name}', 'displayName': display, 'type': media, 'url': path if path.startswith('https://') else url(path), 'representativeQueries': queries})
    ard = {'specVersion': '1.0', 'host': {'displayName': 'Alexander Young', 'identifier': 'youngcrc.com'}, 'entries': entries}
    write('.well-known/ai-catalog.json', ard)
    write('.well-known/ard.json', ard)
    card = {'$schema': 'https://static.modelcontextprotocol.io/schemas/v1/server-card.schema.json', 'name': 'com.youngcrc/research-data', 'version': '1.0.0', 'description': 'Read public cancer-case reports, timeline and research data with provenance.', 'remotes': [{'type': 'streamable-http', 'url': MCP_URL, 'supportedProtocolVersions': ['2025-11-25']}]}
    write('mcp/server-card', card)
    write('.well-known/mcp/server-card.json', card)
    print(json.dumps({'generated_files': len(list(OUT.rglob('*.*'))) + 2, 'reports': len(reports), 'timeline_events': len(timeline), 'datasets': len(catalogue), 'markdown_bytes': (OUT / 'agents/case.md').stat().st_size}))

if __name__ == '__main__':
    build()
