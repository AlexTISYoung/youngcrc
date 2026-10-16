'use strict';

(() => {
  const host = document.getElementById('laboratory-browser');
  if (!host) return;
  const PAGE_SIZE = 50;
  const records = value => Array.isArray(value) ? value : value.records || [];
  const node = (tag, text) => { const item = document.createElement(tag); if (text !== undefined) item.textContent = text; return item; };
  const shown = value => value === null || value === undefined || value === '' ? 'Not recorded' : String(value);
  const sourceById = new Map();
  let observations = [], page = 0;
  const controls = node('div'); controls.className = 'filter-row';
  function control(labelText, tag, id) {
    const label = node('label', labelText), item = node(tag); item.id = id;
    label.htmlFor = id; label.append(item); controls.append(label); return item;
  }
  const search = control('Find a result', 'input', 'laboratory-search'); search.type = 'search'; search.placeholder = 'Search analyte, panel or assay…';
  const institution = control('Institution', 'select', 'laboratory-institution');
  const analyte = control('Analyte / assay label', 'select', 'laboratory-analyte');
  const order = control('Date order', 'select', 'laboratory-order');
  [['newest', 'Newest first'], ['oldest', 'Oldest first']].forEach(([value, text]) => { const item = node('option', text); item.value = value; order.append(item); });
  const count = node('p'); count.id = 'laboratory-count'; count.setAttribute('aria-live', 'polite');
  const tableHost = node('div'), pager = node('div'); pager.className = 'filter-row';
  const previous = node('button', 'Previous'), next = node('button', 'Next'), pageText = node('span');
  previous.type = next.type = 'button'; previous.className = next.className = 'button'; pager.append(previous, pageText, next);
  host.append(controls, count, tableHost, pager);

  function options(select, values, all) {
    const option = node('option', all); option.value = ''; select.append(option);
    [...new Set(values)].sort((a, b) => a.localeCompare(b)).forEach(value => { const item = node('option', value); item.value = value; select.append(item); });
  }
  function details(row) {
    const item = node('details'); item.append(node('summary', 'Result & sources'));
    const sourceIds = row.source_ids || (row.source_id ? [row.source_id] : []);
    const title = node('p', sourceIds.map(id => `${id}: ${sourceById.get(id)?.title || 'Source title unavailable'}`).join('; '));
    item.append(title);
    sourceIds.forEach(id => {
      const source = sourceById.get(id);
      if (source?.public_prepared_path) {
        const paragraph = node('p'), link = node('a', 'View prepared report PDF');
        link.href = source.public_prepared_path; paragraph.append(link); item.append(paragraph);
      }
    });
    if (row.assay_method_as_reported || row.assay_method) item.append(node('p', row.assay_method_as_reported || row.assay_method));
    item.append(node('pre', JSON.stringify(row, null, 2))); return item;
  }
  function reportGroup(title, rows, columns, path, note) {
    const heading = node('div'); heading.className = 'group-title'; heading.append(node('h3', title));
    const download = node('a', 'Download JSON'); download.href = path; download.download = ''; heading.append(download);
    host.append(heading, node('p', note));
    const wrapper = node('div'); wrapper.className = 'table-wrap'; wrapper.tabIndex = 0; wrapper.setAttribute('role', 'region'); wrapper.setAttribute('aria-label', title);
    const table = node('table'), head = node('thead'), header = node('tr'), body = node('tbody');
    [...columns.map(column => column.label), 'Evidence'].forEach(text => { const cell = node('th', text); cell.scope = 'col'; header.append(cell); });
    head.append(header); table.append(head);
    rows.forEach(row => { const tr = node('tr'); columns.forEach(column => tr.append(node('td', column.value(row)))); const cell = node('td'); cell.append(details(row)); tr.append(cell); body.append(tr); });
    table.append(body); wrapper.append(table); host.append(wrapper);
  }
  async function drawSeparateAssays() {
    try {
      const paths = ['data/clinical/liquid_biopsy_observations.json', 'data/clinical/plasma_profiling_assays.json'];
      const [liquid, plasma] = await Promise.all(paths.map(async path => { const response = await fetch(path); if (!response.ok) throw new Error('Unavailable assay dataset'); return response.json(); }));
      reportGroup('Personalis / Tempus xM', records(liquid), [
        {label:'Collection', value:row => shown(row.date)}, {label:'Assay / specimen', value:row => `${row.assay} · ${row.specimen}`}, {label:'Reported result', value:row => `${row.value} ${row.unit} · ${row.result}`}, {label:'Report date', value:row => shown(row.report_date)}, {label:'Source notes', value:row => row.notes}
      ], paths[0], 'This assay reports PPM, distinct from Signatera MTM/mL. Source notes retain the corrected draw date and conflicting amendment year.');
      reportGroup('Plasma profiling reports', records(plasma), [
        {label:'Collection', value:row => shown(row.collection_date)}, {label:'Assay / specimen', value:row => `${row.assay} · ${row.specimen}`}, {label:'Report date', value:row => shown(row.report_date)}, {label:'Reported findings', value:row => row.findings.map(finding => `${finding.feature}: ${finding.comparator || ''}${finding.value}${finding.unit ? ' ' + finding.unit : ''}${finding.classification ? ' (' + finding.classification + ')' : ''}${finding.interpretation_as_reported ? ' (' + finding.interpretation_as_reported + ')' : ''}`).join('; ')}, {label:'Report limits', value:row => row.limitations.join(' ')}
      ], paths[1], 'Low tumour signal limits negative or indeterminate plasma results; these cannot rule out cancer or establish tumour genotype. Pharmacogenomic entries reproduce reported observations.');
    } catch { host.append(node('p', 'Additional plasma-assay tables could not be loaded.')); }
  }
  function draw() {
    const query = search.value.trim().toLocaleLowerCase();
    const filtered = observations.filter(row => (!institution.value || (row.institution || 'Not recorded') === institution.value) && (!analyte.value || row.analyte === analyte.value) && [row.analyte, row.panel_label_as_reported, row.series_label_as_reported, row.assay_method_as_reported, row.context].filter(Boolean).join(' ').toLocaleLowerCase().includes(query));
    filtered.sort((a, b) => {
      const ad = a.collection_datetime || a.date || '', bd = b.collection_datetime || b.date || '';
      if (!ad) return bd ? 1 : String(a.id).localeCompare(String(b.id));
      if (!bd) return -1;
      const dates = ad.localeCompare(bd) * (order.value === 'oldest' ? 1 : -1);
      return dates || String(a.id).localeCompare(String(b.id));
    });
    const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)); page = Math.min(page, pages - 1);
    const rows = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
    count.textContent = `${filtered.length.toLocaleString()} of ${observations.length.toLocaleString()} measurements`;
    previous.disabled = page === 0; next.disabled = page === pages - 1; pageText.textContent = `Page ${page + 1} of ${pages}`;
    tableHost.replaceChildren();
    if (!rows.length) { tableHost.append(node('p', 'No measurements match these filters.')); return; }
    const wrapper = node('div'); wrapper.className = 'table-wrap'; wrapper.tabIndex = 0; wrapper.setAttribute('role', 'region'); wrapper.setAttribute('aria-label', 'Filtered laboratory measurements');
    const table = node('table'), head = node('thead'), header = node('tr');
    ['Reported date / time', 'Analyte', 'Reported result', 'Reported reference range', 'Reported flag', 'Institution', 'Evidence'].forEach(text => { const cell = node('th', text); cell.scope = 'col'; header.append(cell); });
    head.append(header); table.append(head); const body = node('tbody');
    rows.forEach(row => {
      const tr = node('tr');
      const date = row.collection_datetime || row.date;
      const resultValue = row.value_as_reported || `${row.comparator || ''}${shown(row.value)}`;
      const result = resultValue + (row.unit && !resultValue.includes(row.unit) ? ' ' + row.unit : '');
      const dateText = shown(date) + (/collection_role_unconfirmed/.test(row.date_basis || '') ? ' (date role unconfirmed)' : '');
      [dateText, shown(row.analyte), result, shown(row.reference_range_as_reported), shown(row.flag_as_reported), shown(row.institution)].forEach(text => tr.append(node('td', text)));
      const evidence = node('td'); evidence.append(details(row)); tr.append(evidence); body.append(tr);
    });
    table.append(body); wrapper.append(table); tableHost.append(wrapper);
  }
  [search, institution, analyte, order].forEach(item => item.addEventListener(item === search ? 'input' : 'change', () => { page = 0; draw(); }));
  previous.addEventListener('click', () => { page = Math.max(0, page - 1); draw(); });
  next.addEventListener('click', () => { page += 1; draw(); });
  Promise.all(['data/clinical/laboratory_observations.json', 'data/clinical/sources.json'].map(async path => {
    const response = await fetch(path); if (!response.ok) throw new Error('Unavailable laboratory dataset'); return response.json();
  })).then(([labs, sources]) => {
    observations = records(labs); records(sources).forEach(source => sourceById.set(source.id, source));
    options(institution, observations.map(row => row.institution || 'Not recorded'), 'All institutions');
    options(analyte, observations.map(row => row.analyte), 'All analytes'); draw(); drawSeparateAssays();
  }).catch(() => { count.textContent = 'The laboratory table could not be loaded. The JSON download remains linked above.'; controls.hidden = pager.hidden = true; });
})();
