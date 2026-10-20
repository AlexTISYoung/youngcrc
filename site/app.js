'use strict';

const $ = (selector) => document.querySelector(selector);
const sections = ['overview', 'timeline', 'reports', 'molecular', 'sequencing', 'pathology', 'imaging', 'research', 'methods', 'contact'];
const caseTitle = 'Alexander Young: early onset metastatic rectal cancer case';
const sectionLabels = {overview:'Overview', timeline:'Clinical timeline', sequencing:'Sequencing', pathology:'Pathology', imaging:'Imaging', molecular:'Molecular evidence', reports:'Reports', research:'Research & documentation', methods:'Use & provenance', contact:'Contact'};
const records = (value) => Array.isArray(value) ? value : (value.records || []);
const el = (tag, text, className) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; };
const human = (key) => key.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
const valueText = (value) => value === null || value === undefined || value === '' ? 'Not recorded' : typeof value === 'object' ? (Array.isArray(value) ? value.map(valueText).join('; ') : JSON.stringify(value)) : String(value);
const first = (record, keys, fallback = '') => { for (const key of keys) if (record[key] !== null && record[key] !== undefined && record[key] !== '') return valueText(record[key]); return fallback; };
const bytes = (n) => n === null || n === undefined ? 'Not recorded' : n === 0 ? '0 B' : n >= 1e9 ? `${(n / 1e9).toFixed(2)} GB` : n >= 1e6 ? `${(n / 1e6).toFixed(2)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`;

function downloadLink(item, label, openReport = false) {
  const target = item.download_url || item.path;
  if (!target) return el('span', 'Not yet available');
  const url = new URL(target, document.baseURI);
  if (!['https:', 'http:'].includes(url.protocol) || (url.origin !== location.origin && url.protocol !== 'https:')) return el('span', 'Unavailable link');
  const a = el('a', label);
  a.href = url.href;
  a.rel = 'noopener noreferrer';
  a.referrerPolicy = 'no-referrer';
  if (openReport) a.target = '_blank';
  else if (url.origin === location.origin) a.download = '';
  return a;
}

function route() {
  const hash = location.hash.slice(1);
  const aliases = {catalogue:'sequencing', dna:'sequencing', rna:'sequencing', laboratory:'timeline'};
  const requested = aliases[hash] || hash;
  const name = sections.includes(requested) ? requested : 'overview';
  sections.forEach((id) => { document.getElementById(id).hidden = id !== name; });
  document.querySelectorAll('.nav-inner a').forEach((a) => a.getAttribute('href') === `#${name}` ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
  document.title = name === 'overview' ? caseTitle : `${sectionLabels[name]} | ${caseTitle}`;
  if (hash === 'rna' || hash === 'dna') activateSubtab(document.getElementById(`${hash}-tab`));
  if (hash === 'laboratory') activateSubtab(document.getElementById('clinical-labs-tab'));
}
function activateSubtab(button, focus = false) {
  const tablist = button.closest('[role="tablist"]');
  tablist.querySelectorAll('[role="tab"]').forEach(tab => {
    const selected = tab === button;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(tab.dataset.subtab).hidden = !selected;
  });
  if (focus) button.focus();
}
document.querySelectorAll('.subtabs').forEach(tablist => {
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateSubtab(tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); activateSubtab(tabs[next], true); }
    });
  });
});
window.addEventListener('hashchange', route);
route();

const contactReturnUrl = new URL(location.href);
if (contactReturnUrl.searchParams.get('contact') === 'submitted') {
  const status = document.getElementById('contact-status');
  status.hidden = false;
  status.textContent = 'Thank you — your message has been submitted.';
  contactReturnUrl.searchParams.delete('contact');
  history.replaceState(history.state, '', contactReturnUrl.pathname + contactReturnUrl.search + contactReturnUrl.hash);
}

function detail(record) {
  const wrapper = el('details');
  wrapper.append(el('summary', 'Full record & sources'), el('pre', JSON.stringify(record, null, 2)));
  return wrapper;
}

function makeTable(rows, columns, caption) {
  if (!rows.length) return el('p', 'No records are available in this release.', 'empty');
  const wrap = el('div', undefined, 'table-wrap');
  wrap.tabIndex = 0;
  wrap.setAttribute('role', 'region');
  wrap.setAttribute('aria-label', caption);
  const table = el('table');
  const thead = el('thead'); const header = el('tr');
  columns.forEach((c) => {const th = el('th', c.label); th.scope = 'col'; header.append(th);});
  const finalHeader = el('th', 'Evidence'); finalHeader.scope = 'col'; header.append(finalHeader);
  thead.append(header); table.append(thead);
  const body = el('tbody');
  rows.forEach((r) => {
    const tr = el('tr');
    columns.forEach((c) => { const td = el('td'); if (c.render) td.append(c.render(r)); else { const value = c.format ? c.format(r) : first(r, c.keys, 'Not recorded'); td.textContent = String(value).replaceAll('_', ' '); } tr.append(td); });
    const td = el('td'); td.append(detail(r)); tr.append(td); body.append(tr);
  });
  table.append(body); wrap.append(table); return wrap;
}

function group(container, title, rows, columns, path) {
  const heading = el('div', undefined, 'group-title'); heading.append(el('h3', title));
  const a = el('a', 'Download JSON'); a.href = path; a.download = ''; heading.append(a);
  container.append(heading, makeTable(rows, columns, title));
}

function drawTimeline(data) {
  const container = $('#timeline-content');
  records(data).forEach((r) => {
    const item = el('article', undefined, 'timeline-item');
    const date = el('time', first(r, ['date', 'start_date', 'date_display'], 'Date unconfirmed') + (r.end_date ? ' – ' + r.end_date : ''));
    if (/^\d{4}-\d{2}-\d{2}$/.test(r.date || '')) date.dateTime = r.date;
    const body = el('div', undefined, 'timeline-entry');
    body.append(el('h3', first(r, ['title', 'event', 'category'], 'Clinical event')), el('p', first(r, ['summary', 'description'])));
    const status = first(r, ['status', 'evidence_status', 'date_basis']);
    if (status) body.append(el('p', status.replaceAll('_', ' ').replace(/^patient reported /, 'my reported '), 'evidence'));
    body.append(detail(r)); item.append(date, body); container.append(item);
  });
}

let catalogue = [], providers = [], reports = [], inventory = [];
function specimenText(item) {
  const rows = item.specimens || [];
  return rows.length ? rows.map(s => `${s.label} (${s.sample_id}) · ${s.collection_date ? 'collected ' + s.collection_date : 'collection date unconfirmed'}`).join('; ') : (item.specimen_description || 'Multiple specimens / see individual source records');
}
function referenceLabel(item) {
  if (item.reference_label) return item.reference_label;
  const labels = {
    GRCh38_dictionary_family_exact_FASTA_unconfirmed: 'GRCh38 family; exact reference unconfirmed',
    GRCh37_dictionary_family_exact_FASTA_unconfirmed: 'GRCh37 family; exact reference unconfirmed',
    hg38_custom_masked_noHap: 'Custom masked hg38; exact reference unconfirmed',
    source_sequence_dictionary_exact_FASTA_unconfirmed: 'Source reference; exact FASTA unconfirmed',
    unverified: 'Reference unconfirmed'
  };
  if (item.reference_build === 'source_VCF_reference_metadata_exact_FASTA_unconfirmed') {
    return item.reference_identifier === 'hg38.pU2AF1_Y_PAR_masked.noHap.fa'
      ? 'Custom masked hg38; exact reference unconfirmed' : 'Source reference; exact FASTA unconfirmed';
  }
  return labels[item.reference_build] || item.reference_build || '';
}
function provenanceBlock(item) {
  const box = el('div', undefined, 'provenance-block');
  box.append(el('p', specimenText(item), 'specimen-label'));
  const reference = referenceLabel(item);
  if (item.assay_label) box.append(el('p', item.assay_label + (reference ? ` · ${reference}` : '')));
  const cellFreeFile = item.provider_id === 'caris' && item.release_file_id &&
    ['M-ASSAY-009', 'M-ASSAY-021'].includes(item.assay_id);
  const caveat = cellFreeFile ? 'Exact tube and library details remain unconfirmed.' :
    item.path === 'data/molecular/caris_delivery_status.json' ?
      '15 announced files were not retrievable through the Caris connection on 19 October 2026.' : null;
  if (caveat) box.append(el('p', caveat, 'source-note'));
  else if (item.provenance_summary && item.provenance_summary !== item.description) box.append(el('p', item.provenance_summary));
  return box;
}
function providerHeading(provider, count, noun = 'file') {
  const header = el('div', undefined, 'provider-heading');
  header.append(el('h4', provider.name), el('span', `${count} ${count === 1 ? noun : noun + 's'}`, 'tag'));
  return header;
}
function fillProviderSelect(select, providerIds) {
  providers.filter(p => providerIds.includes(p.provider_id)).forEach(p => { const option = el('option', p.name); option.value = p.provider_id; select.append(option); });
}
function searchText(item) {
  return [item.title, item.description, item.format, item.path, item.filename, item.release_file_id, item.file_id, item.provider, specimenText(item), item.assay_label, item.browse_type, item.role, ...(item.result_summary?.findings || []), item.result_summary?.note].join(' ').toLowerCase();
}
function groupedFiles(container, items, render, noun = 'file') {
  const types = [...new Set(items.map(r => r.browse_type))].sort((a,b) => a.localeCompare(b));
  types.forEach(type => {
    const section = el('section', undefined, 'subtype-group');
    section.append(el('h3', type, 'subtype-heading'));
    providers.forEach(provider => {
      const rows = items.filter(r => r.browse_type === type && r.provider_id === provider.provider_id);
      if (!rows.length) return;
      const subgroup = el('div', undefined, 'provider-group');
      subgroup.append(providerHeading(provider, rows.length, noun), render(rows, provider, type));
      section.append(subgroup);
    });
    container.append(section);
  });
}
function drawRawInventory(browser, query, providerId) {
  const modality = browser.dataset.modality;
  const container = browser.querySelector('[data-raw-inventory]'); container.replaceChildren();
  const all = inventory.filter(r => r.browse_modality === modality);
  browser.querySelector('[data-raw-section]').hidden = !all.length;
  const rows = all.filter(r => (!providerId || r.provider_id === providerId) && searchText(r).includes(query));
  groupedFiles(container, rows, (items, p, type) => makeTable(items, [
    {label:'File / assay',format:r=>`${r.file_id} · ${r.assay_label || r.role}`}, {label:'Specimen',format:specimenText}, {label:'Format',keys:['format']}, {label:'Source size',format:r=>bytes(r.logical_bytes ?? r.bytes)}, {label:'Status',format:r=>r.preparation_label || (r.download_url ? 'Public download verified' : 'Pending preparation / verification')}, {label:'Download',render:r=>downloadLink(r, r.released_filename || 'Download file')}
  ], `${type} · ${p.name} ${modality === 'molecular' ? 'molecular source' : 'sequencing'} inventory`));
  if (all.length && !rows.length) container.append(el('p', 'No source files match this search.', 'empty'));
}
function datasetCards(rows) {
  const cards = el('div', undefined, 'dataset-list');
  rows.forEach(item => {
    const card = el('article', undefined, 'dataset-card');
    card.append(el('span', item.browse_type, 'eyebrow'), el('h4', item.title), el('p', item.description), provenanceBlock(item));
    card.append(el('span', `${item.format} · ${bytes(item.bytes)}${item.record_count == null ? '' : ` · ${item.record_count} records`}`, 'file-meta'));
    card.append(downloadLink(item, `Download ${item.format}`), detail(item)); cards.append(card);
  });
  return cards;
}
function drawCatalogue(browser) {
  const query = browser.querySelector('[data-dataset-search]').value.toLowerCase().trim();
  const providerId = browser.querySelector('[data-provider-filter]').value;
  const all = catalogue.filter(item => item.browse_modality === browser.dataset.modality);
  const items = all.filter(item => (!providerId || item.provider_id === providerId) && searchText(item).includes(query));
  const list = browser.querySelector('[data-dataset-catalogue]'); list.replaceChildren();
  browser.querySelector('[data-catalogue-count]').textContent = `${items.length} of ${all.length} datasets`;
  groupedFiles(list, items, datasetCards);
  if (!items.length) list.append(el('p', 'No datasets match this search.', 'empty'));
  drawRawInventory(browser, query, providerId);
}
function reportCards(rows) {
  const cards=el('div',undefined,'dataset-list');
  rows.forEach(r=>{
    const card=el('article',undefined,'dataset-card');
    const imaging = reportModality(r) === 'imaging';
    const label = imaging ? (r.report_status === 'image_storage_entry' ? 'Image-storage entry' : r.format === 'HTML' ? 'Full portal report' : 'Source report') : r.evidence_class || 'Source report';
    card.append(el('span',label,'eyebrow'),el('h4',r.title),el('p',r.description));
    if (imaging) {
      const date = r.chronology_date || r.study_date || r.report_date;
      const dateLabel = r.study_date ? 'Study date' : date === r.report_date ? 'Report date' : 'Portal-listed date';
      card.append(el('p',`${dateLabel}: ${date || 'not stated / unconfirmed'}`, 'report-date'));
      if (r.report_date && r.report_date !== date) card.append(el('p',`Report date: ${r.report_date}`, 'report-date'));
      if (r.provenance_summary) card.append(el('p',r.provenance_summary,'source-note'));
    } else {
      card.append(provenanceBlock(r),el('p',`Report date: ${r.report_date || 'not stated / unconfirmed'}`, 'report-date'));
    }
    if (r.result_summary) {
      const results = el('div', undefined, 'report-results');
      results.append(el('h5', 'Key findings'));
      const findings = el('ul');
      r.result_summary.findings.forEach(finding => findings.append(el('li', finding)));
      results.append(findings);
      if (r.result_summary.note) results.append(el('p', r.result_summary.note, 'summary-note'));
      const source = el('p', undefined, 'summary-source');
      const pages = r.result_summary.pages;
      const label = pages ? `Source: report ${pages.length === 1 ? 'page' : 'pages'} ${pages.join(', ')}` : `Source: ${r.result_summary.section}`;
      source.append(downloadLink({path: pages ? `${r.path}#page=${pages[0]}` : r.path}, label, true));
      results.append(source); card.append(results);
    }
    if(r.path || r.download_url) card.append(el('span',`${r.format} · ${bytes(r.bytes)}`,'file-meta'),downloadLink(r,r.format === 'HTML' ? 'Open HTML report' : `Download ${r.format}`,r.format === 'HTML'));
    else card.append(el('span',r.availability_note || r.status_label || 'Report not supplied','status'));
    if(r.table_download_url) card.append(downloadLink({path:r.table_download_url}, 'Download table CSV'));
    if(r.bundle_download_url) card.append(downloadLink({path:r.bundle_download_url}, 'Download complete source ZIP'));
    card.append(detail(r)); cards.append(card);
  });
  return cards;
}
function reportModality(report) {
  if (report.browse_type.startsWith('Imaging ·')) return 'imaging';
  if (report.browse_type.startsWith('Pathology ·')) return 'pathology';
  return 'general';
}
function drawReports(browser) {
  const query = browser.querySelector('[data-report-search]').value.toLowerCase().trim();
  const providerId = browser.querySelector('[data-report-provider]').value, type = browser.querySelector('[data-report-type]').value;
  const list = browser.querySelector('[data-report-catalogue]'); list.replaceChildren();
  const all = reports.filter(r => reportModality(r) === browser.dataset.reportModality);
  const filtered = all.filter(r => (!providerId || r.provider_id === providerId) && (!type || r.browse_type === type) && searchText(r).includes(query));
  const noun = browser.dataset.reportModality === 'imaging' ? 'imaging entries' : 'reports';
  browser.querySelector('[data-report-count]').textContent = `${filtered.length} of ${all.length} ${noun}`;
  if (browser.dataset.reportModality === 'imaging') {
    const dateKey = report => [report.chronology_date, report.study_date, report.report_date].find(date => /^\d{4}-\d{2}-\d{2}$/.test(date || '')) || '';
    filtered.sort((a, b) => dateKey(b).localeCompare(dateKey(a)));
    list.append(reportCards(filtered));
  } else {
    groupedFiles(list, filtered, reportCards, 'report');
  }
  if(!filtered.length) list.append(el('p','No reports match this search.','empty'));
}

async function get(path) {
  const response = await fetch(`${path}?release=v1.41`);
  if (!response.ok) throw new Error(`Unavailable dataset: ${path}`);
  return response.json();
}

function treatmentLinks(links) {
  const list = el('ul', undefined, 'treatment-links');
  links.forEach(link => {
    const item = el('li');
    item.append(downloadLink({path:link.url}, link.label, true));
    list.append(item);
  });
  return list;
}

function evidenceParagraph(container, label, text) {
  const paragraph = el('p');
  paragraph.append(el('strong', `${label} `), document.createTextNode(text));
  container.append(paragraph);
}

function shortlistTable(rows, caption, approachLabel = 'Candidate / approach', includeCase = false) {
  const wrapper = el('div', undefined, 'shortlist-table-wrap');
  const table = el('table', undefined, 'shortlist-table');
  if (includeCase) table.classList.add('established-table');
  table.append(el('caption', caption));
  const head = el('thead'), headRow = el('tr');
  const evidenceLabel = includeCase ? 'Published evidence' : 'Why it merits discussion';
  const columns = [approachLabel, evidenceLabel, ...(includeCase ? ['Relevance to my case'] : []), 'Access / main limitation'];
  columns.forEach(label => {
    const cell = el('th', label); cell.scope = 'col'; headRow.append(cell);
  });
  head.append(headRow); table.append(head);
  const body = el('tbody');
  rows.forEach(row => {
    const tr = el('tr'), name = el('th'), evidence = el('td'), access = el('td');
    name.scope = 'row';
    name.append(el('span', row.candidate, 'shortlist-name'), el('span', row.mechanism, 'shortlist-mechanism'));
    const citations = el('details', undefined, 'shortlist-sources');
    citations.append(el('summary', 'Sources'), treatmentLinks(row.sources));
    name.append(citations);
    evidence.dataset.label = evidenceLabel;
    evidence.append(el('span', row.evidence_type, 'shortlist-evidence-type'), el('p', row.evidence));
    access.dataset.label = 'Access / main limitation';
    access.append(el('p', row.access), el('p', row.caveat, 'shortlist-caveat'));
    if (row.details) {
      const details = el('details', undefined, 'shortlist-detail');
      details.append(el('summary', includeCase ? 'Evidence and considerations' : 'Evidence and eligibility'));
      evidenceParagraph(details, 'My evidence:', row.details.patient_evidence);
      evidenceParagraph(details, 'Clinical evidence:', row.details.clinical_evidence);
      evidenceParagraph(details, 'Eligibility and access:', row.details.access);
      evidenceParagraph(details, 'Sequencing:', row.details.timing);
      details.append(el('p', row.details.evidence_level, 'source-note'));
      access.append(details);
    }
    tr.append(name, evidence);
    if (includeCase) {
      const relevance = el('td'); relevance.dataset.label = 'Relevance to my case';
      relevance.append(el('p', row.case_relevance)); tr.append(relevance);
    }
    tr.append(access); body.append(tr);
  });
  table.append(body); wrapper.append(table); return wrapper;
}

function drawShortlist(data) {
  const section = el('section', undefined, 'therapeutic-shortlist');
  section.id = 'therapeutic-shortlist';
  section.setAttribute('aria-labelledby', 'shortlist-heading');
  const heading = el('h4', data.title); heading.id = 'shortlist-heading';
  section.append(heading, el('p', data.intro, 'shortlist-intro'));
  section.append(shortlistTable([...data.drug_rows, ...data.cell_rows], 'Potential drugs and cellular therapies'));
  const context = el('div', undefined, 'shortlist-context');
  context.append(el('p', data.benchmark));
  const details = el('details'); details.append(el('summary', 'Access considerations'));
  data.shared_caveats.forEach(note => details.append(el('p', note)));
  context.append(details); section.append(context); return section;
}

function drawEstablishedTreatments(data) {
  const section = el('section', undefined, 'therapeutic-shortlist');
  section.id = 'established-later-line-treatments';
  section.setAttribute('aria-labelledby', 'established-treatments-heading');
  const heading = el('h4', 'Established later-line treatments');
  heading.id = 'established-treatments-heading';
  section.append(heading, el('p', data.established_intro, 'shortlist-intro'));
  section.append(shortlistTable(data.established_rows, 'Evidence and UK access reviewed 8 October 2026', 'Treatment / approach', true));
  section.append(el('p', data.established_evidence_note, 'source-note'));
  const other = el('details', undefined, 'established-other');
  other.append(el('summary', 'Other marketed combinations reviewed'));
  data.additional_established_options.forEach(option => {
    const item = el('div');
    evidenceParagraph(item, `${option.title}:`, option.body);
    item.append(treatmentLinks(option.sources)); other.append(item);
  });
  section.append(other);
  return section;
}

function drawTreatments(data) {
  const container = $('#treatment-content');
  container.append(el('p', data.introduction, 'source-note'), el('h4', 'My current treatment and vaccine plans', 'treatment-subheading'));
  const plans = el('div', undefined, 'treatment-plans');
  data.plans.forEach(plan => {
    const card = el('article', undefined, 'treatment-card');
    card.append(el('span', plan.status_label, 'treatment-status'), el('h4', plan.title), el('p', plan.body));
    const evidence = el('details');
    evidence.append(el('summary', 'Rationale, evidence and timing'));
    evidenceParagraph(evidence, 'My evidence:', plan.rationale);
    evidenceParagraph(evidence, 'Clinical evidence:', plan.evidence_summary);
    evidenceParagraph(evidence, 'Timing:', plan.timing);
    evidenceParagraph(evidence, 'Evidence to resolve:', plan.evidence_needed);
    evidence.append(el('p', plan.public_caveat, 'source-note'), treatmentLinks(plan.links));
    card.append(evidence);
    plans.append(card);
  });
  container.append(plans, drawShortlist(data.shortlist), drawEstablishedTreatments(data.shortlist));
  if (data.sequencing_note) container.append(el('p', data.sequencing_note, 'source-note'));
  if (['#therapeutic-shortlist', '#established-later-line-treatments'].includes(location.hash)) document.getElementById(location.hash.slice(1)).scrollIntoView();
}

function molecularSources(sources = []) {
  const block = el('details', undefined, 'molecular-evidence');
  block.append(el('summary', 'Sources and assay details'));
  const list = el('ul');
  sources.forEach(source => {
    const item = el('li');
    const report = reports.find(r => r.report_id === source.report_id);
    const provider = report && providers.find(p => p.provider_id === report.provider_id);
    const label = source.label || (provider ? `${provider.name} report` : source.report_id || 'Source data');
    let target = source.url || source.report_url;
    if (target && source.pages?.length && !target.includes('#')) target += `#page=${source.pages[0]}`;
    if (target) item.append(downloadLink({path:target}, label, true));
    else item.append(document.createTextNode(label));
    const ids = [source.report_id, ...(source.source_ids || (source.source_id ? [source.source_id] : [])), source.sample_id, source.assay_id, ...(source.record_ids || [])].filter(Boolean);
    const notes = [source.pages?.length ? `pages ${source.pages.join(', ')}` : '', ...ids, source.collection_date ? `collected ${source.collection_date}` : ''].filter(Boolean);
    if (notes.length) item.append(el('span', notes.join(' · '), 'source-note'));
    list.append(item);
  });
  block.append(list);
  return block;
}

function molecularTable(rows, columns, caption) {
  const wrap = el('div', undefined, 'molecular-table-wrap');
  const table = el('table', undefined, 'molecular-table');
  table.append(el('caption', caption));
  const head = el('thead'), header = el('tr');
  columns.forEach(column => { const cell = el('th', column.label); cell.scope = 'col'; header.append(cell); });
  head.append(header); table.append(head);
  const body = el('tbody');
  rows.forEach(row => {
    const tr = el('tr');
    columns.forEach((column, index) => {
      const cell = el(index === 0 ? 'th' : 'td');
      if (index === 0) cell.scope = 'row';
      else cell.dataset.label = column.label;
      const value = column.render ? column.render(row) : el('p', row[column.key]);
      cell.append(value); tr.append(cell);
    });
    body.append(tr);
  });
  table.append(body); wrap.append(table);
  return wrap;
}

function molecularText(text, sources = []) {
  const node = el('div'); node.append(el('p', text));
  if (sources.length) node.append(molecularSources(sources));
  return node;
}

function vaccineSequenceDetails(row) {
  const box = el('div');
  if (row.sequence_notes?.length) row.sequence_notes.forEach(note => box.append(el('p', note, 'molecular-alert')));
  const details = el('details', undefined, 'vaccine-sequences');
  details.append(el('summary', 'Peptides and supporting evidence'));
  for (const [provider, record] of [['JLF', row.jlf], ['Invoke', row.invoke]]) {
    if (!record) continue;
    details.append(el('h5', provider));
    for (const [label, value] of [['Precursor', record.full_precursor || record.full_peptide], ['Class I window', record.class_i_epitope], ['Class II window', record.class_ii_epitope]]) {
      if (!value) continue;
      const p = el('p'); p.append(el('span', `${label}: `), el('code', value)); details.append(p);
    }
    if (provider === 'Invoke') details.append(el('p', 'Candidate-specific HLA allele restrictions are not supplied by this table.', 'source-note'));
  }
  (row.research_audits || []).forEach(audit => {
    details.append(el('p', `${audit.evidence_id}: ${audit.summary} ${audit.assessment}`, 'vaccine-audit'));
    if (audit.research_sequence) { const p = el('p'); p.append(el('span', 'Audit sequence: '), el('code', audit.research_sequence)); details.append(p); }
  });
  details.append(molecularSources([row.jlf, row.invoke].filter(Boolean).map(record => ({report_id:record.report_id, source_id:record.source_id, url:record.report_url}))));
  box.append(details); return box;
}

function vaccineTable(rows, caption, includeJlf = true) {
  const columns = [
    {label:'Target', render:r=>{ const box = el('div'); box.append(el('strong', `${r.gene} ${r.protein_change}`, 'molecular-name')); if (r.jlf) box.append(el('span', `JLF design ${r.jlf.source_row_number}`, 'source-note')); return box; }},
    {label:'JLF design', render:r=>{ const box=el('div'); if (!r.jlf) box.append(el('p', 'Not in the 20-design list')); else { box.append(el('p', r.jlf.hla_restriction), el('code', r.jlf.class_i_epitope)); if (r.jlf.class_ii_epitope) box.append(el('p', 'Also includes a class II window', 'source-note')); } return box; }},
    {label:'Invoke prediction', render:r=>{ const box=el('div'); box.append(el('strong', `Tier ${r.invoke.tier} · rank ${r.invoke.rank}`), el('p', `RNA AF: ${r.invoke.rna_af_display ?? 'Not reported'} · TPM: ${r.invoke.rna_tpm_display}`)); return box; }},
    {label:'Sequence evidence', render:vaccineSequenceDetails}
  ];
  return molecularTable(rows, includeJlf ? columns : columns.filter(column=>column.label !== 'JLF design'), caption);
}

function drawMolecular(data) {
  const container = $('#molecular-summary');
  const overview = el('div', undefined, 'molecular-profile');
  data.overview.forEach(fact => { const card=el('article'); card.append(el('h3', fact.title), el('p', fact.text)); overview.append(card); });
  container.append(overview, el('p', data.context_note, 'molecular-context'), el('p', data.variant_count_note, 'molecular-section-note'));
  data.variant_groups.forEach(group => {
    const section = el('section', undefined, 'molecular-section');
    section.append(el('h3', group.title), el('p', group.note, 'molecular-section-note'));
    section.append(molecularTable(group.records, [
      {label:'Variant', render:r=>{ const box=el('div'); box.append(el('strong', r.variant, 'molecular-name')); if (r.dna_change && !r.variant.includes(r.dna_change)) box.append(el('span', r.dna_change, 'source-note')); return box; }},
      {label:'Report evidence', render:r=>{ const box=el('div'); r.evidence_lines.forEach(line=>box.append(el('p', line))); if (r.note) box.append(el('p', r.note, 'molecular-alert')); box.append(molecularSources(r.sources)); return box; }},
      {label:'Connection to therapies', render:r=>{ const box=molecularText(r.therapy_connection); if (r.therapy_links?.length) box.append(treatmentLinks(r.therapy_links)); return box; }}
    ], group.title));
    container.append(section);
  });
  const biomarkers=el('section',undefined,'molecular-section');
  biomarkers.append(el('h3','Treatment and immune biomarkers'), molecularTable(data.biomarker_rows,[
    {label:'Marker',key:'biomarker'}, {label:'Finding',key:'summary'}, {label:'Interpretation',render:r=>molecularText(r.therapy_connection,r.sources)}
  ],'Assay-specific biomarkers'));
  container.append(biomarkers);
  const expression=el('section',undefined,'molecular-section');
  expression.append(el('h3','Expression and target staining'), el('p',data.expression_note,'molecular-section-note'));
  expression.append(molecularTable(data.expression_rows,[
    {label:'Target',render:r=>el('strong',r.target,'molecular-name')},
    {label:'RNA by specimen',render:r=>{
      const box=el('div');
      const observations=r.rna_observations || [{specimen:'Liver metastasis · Valius',summary:r.rna_summary}];
      observations.forEach(observation=>box.append(el('strong',observation.specimen),el('p',observation.summary)));
      return box;
    }},
    {label:'Protein / IHC',key:'protein_summary'},
    {label:'Connection to therapies',render:r=>molecularText(r.therapy_connection,r.sources)}
  ],'Archived rectal and liver specimens — collected 22 October 2024'));
  const context=el('details',undefined,'molecular-assay-context');
  context.append(el('summary','Specimen and assay limitations'),el('p',data.specimen_note),molecularSources(data.specimen_sources));
  data.provenance_limits.forEach(note=>context.append(el('p',note)));
  expression.append(context,el('h4','Rectal RNA and immune context'),molecularText(data.bostongene_immunecontext,data.bostongene_sources),el('h4','Pertinent pathology'),molecularText(data.pathology,data.pathology_sources));
  if (data.caris_blood_rna_context) expression.append(el('h4','Caris Assure blood RNA'),molecularText(data.caris_blood_rna_context,data.caris_blood_rna_sources));
  container.append(expression);
  const vaccine=el('section',undefined,'molecular-section');
  vaccine.append(el('h3','Vaccine targets: JLF and Invoke'),el('p',data.vaccine.introduction_first_person,'molecular-section-note'),el('p',data.vaccine.summary));
  const warning=el('div',undefined,'molecular-context');
  warning.append(el('p','Invoke RNA AF and TPM are maxima across available report samples; TPM is gene expression, not mutant-peptide abundance. Candidate-specific sample mapping remains incomplete.'));
  vaccine.append(warning, vaccineTable(data.vaccine.records.filter(r=>r.jlf),'All 20 JLF targets, with their Invoke matches'), vaccineTable(data.vaccine.records.filter(r=>!r.jlf),'Leading Invoke-only targets', false));
  const more=el('details',undefined,'molecular-additional-targets');
  more.append(el('summary',`Other Invoke-only targets (${data.vaccine.remaining_invoke_rows.length})`),vaccineTable(data.vaccine.remaining_invoke_rows.map(invoke=>({gene:invoke.gene,protein_change:invoke.protein_change,invoke})), 'Other Invoke-only targets — all report tiers', false));
  vaccine.append(more,molecularSources(data.vaccine.sources));
  container.append(vaccine);
}

async function main() {
  const paths = ['data/catalogue.json', 'data/clinical/timeline.json', 'data/clinical/imaging.json', 'data/clinical/pathology.json', 'data/molecular/findings.json', 'data/molecular/samples.json', 'data/molecular/assays.json', 'data/molecular/vaccine_evidence.json', 'data/molecular/raw_file_inventory.json', 'data/gaps.json', 'data/providers.json', 'data/reports.json', 'data/clinical/ctdna.json', 'data/clinical/treatment_options.json'];
  const [cat, timeline, imaging, pathology, findings, samples, assays, vaccine, raw, gaps, providerData, reportData, ctdna, treatments] = await Promise.all(paths.map(get));
  catalogue = records(cat); providers = records(providerData); reports = records(reportData); inventory = records(raw);
  const imagingReports = reports.filter(r => reportModality(r) === 'imaging');
  const fullReports = imagingReports.filter(r => r.full_report_available).length;
  const storageEntries = imagingReports.filter(r => r.report_status === 'image_storage_entry').length;
  const unavailableReports = imagingReports.filter(r => r.report_status === 'report_unavailable').length;
  $('#imaging-report-coverage').textContent = `${fullReports} full diagnostic reports, with PDFs and complete portal transcriptions. ${storageEntries} CT simulation entries are for image storage only.${unavailableReports ? ` ${unavailableReports} diagnostic reports remain unavailable.` : ''}`;
  document.querySelectorAll('[data-report-browser]').forEach(browser => {
    const all = reports.filter(r => reportModality(r) === browser.dataset.reportModality);
    fillProviderSelect(browser.querySelector('[data-report-provider]'), all.map(r => r.provider_id));
    [...new Set(all.map(r => r.browse_type))].sort().forEach(type => {
      const option = el('option', type); option.value = type; browser.querySelector('[data-report-type]').append(option);
    });
    browser.querySelector('[data-report-search]').addEventListener('input', () => drawReports(browser));
    browser.querySelector('[data-report-provider]').addEventListener('change', () => drawReports(browser));
    browser.querySelector('[data-report-type]').addEventListener('change', () => drawReports(browser));
    drawReports(browser);
  });
  document.querySelectorAll('.modality-browser').forEach(browser => {
    const modality = browser.dataset.modality;
    fillProviderSelect(browser.querySelector('[data-provider-filter]'), [...catalogue, ...inventory].filter(r => r.browse_modality === modality).map(r => r.provider_id));
    browser.querySelector('[data-dataset-search]').addEventListener('input', () => drawCatalogue(browser));
    browser.querySelector('[data-provider-filter]').addEventListener('change', () => drawCatalogue(browser));
    drawCatalogue(browser);
  });
  drawTimeline(timeline); drawTreatments(treatments);
  window.drawUnifiedTimeline({timeline, imaging, ctdna, laboratory: await get('data/clinical/laboratory_observations.json')});
  drawMolecular(await get('data/molecular/summary.json'));
  group($('#clinical-detail'), 'Signatera ctDNA', records(ctdna), [
    {label:'Blood draw',format:r=>r.date || 'Date not documented'}, {label:'Result',format:r=>`${r.value} ${r.unit}`}, {label:'Evidence',format:r=>r.evidence_type.replaceAll('_',' ')}
  ], 'data/clinical/ctdna.json');
  group($('#imaging-summary'), 'My imaging study summaries', records(imaging), [
    {label:'Date', keys:['study_date','date','scan_date']}, {label:'Study',format:r=>[r.modality,r.region].filter(Boolean).join(' · ')}, {label:'Findings',keys:['summary','findings_summary','findings']}
  ], 'data/clinical/imaging.json');
  group($('#pathology-summary'), 'My pathology summaries', records(pathology), [
    {label:'Collection',keys:['collection_date','date']}, {label:'Specimen',keys:['tissue','specimen','specimen_description','anatomic_site','title']}, {label:'Diagnosis / result',format:r=>r.diagnosis || (r.findings?.HER2_ihc_score !== undefined ? `HER2 ${r.findings.HER2_ihc_score} — ${r.findings.HER2_interpretation} (${r.findings.HER2_scoring_criteria})` : valueText(r.findings))}
  ], 'data/clinical/pathology.json');
  const research = $('#research-content');
  group(research, 'My molecular findings across sources', records(findings), [
    {label:'Target / feature',keys:['gene','target','biomarker','feature','finding']}, {label:'Finding',format:r=>[r.value,r.unit].filter(v=>v!==null&&v!==undefined).join(' ')}, {label:'Evidence class',keys:['evidence_class','evidence_level','evidence_status','status']}
  ], 'data/molecular/findings.json');
  group(research, 'Specimens', records(samples), [
    {label:'Specimen',keys:['public_sample_id','sample_id','id']}, {label:'Collected',keys:['collection_date','date']}, {label:'Tissue',keys:['label','description','anatomical_site','anatomic_site','tissue','specimen_type']}
  ], 'data/molecular/samples.json');
  group(research, 'Assays', records(assays), [
    {label:'Assay',keys:['label','assay_name','name','assay','assay_type','platform']}, {label:'Material',keys:['sample_id','sample_ids','public_sample_id']}, {label:'Reference',keys:['reference_genome','genome_build','reference_build']}
  ], 'data/molecular/assays.json');
  group(research, 'Vaccine research evidence', records(vaccine), [
    {label:'Target',keys:['gene','target']}, {label:'Variant / question',keys:['topic','alteration','variant','title','question']}, {label:'Finding',keys:['summary','finding','evidence_summary','interpretation','conclusion']}
  ], 'data/molecular/vaccine_evidence.json');
  const gapList = el('ul'); records(gaps).forEach((r) => gapList.append(el('li', `${r.title}: ${r.detail}`))); $('#gaps-content').append(gapList);
}
main().catch(() => { $('#load-error').hidden = false; });
