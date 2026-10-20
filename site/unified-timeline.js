'use strict';

(() => {
  const rows = value => Array.isArray(value) ? value : (value?.records || []);
  const node = (tag, text, className) => {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = text;
    if (className) item.className = className;
    return item;
  };
  const recordId = record => record.id || record.observation_id;
  const sourceIds = record => record.source_ids || (record.source_id ? [record.source_id] : []);
  const human = value => String(value || 'Recorded').replaceAll('_', ' ').replace(/^\w/, letter => letter.toUpperCase());
  const numeric = record => typeof record.value === 'number' && Number.isFinite(record.value) && record.value >= 0;
  const dateOf = record => record.collection_date || record.date;
  // Month-precision events occupy the middle of their reported month, with that
  // precision retained in every visible date and accessible marker description.
  function timeOf(date) {
    if (!/^\d{4}-\d{2}(?:-\d{2})?$/.test(date || '')) return null;
    const timestamp = Date.parse(`${date.length === 7 ? date + '-15' : date}T00:00:00Z`);
    return Number.isFinite(timestamp) ? timestamp : null;
  }
  const dateText = date => {
    const time = timeOf(date);
    if (time === null) return 'Date not supplied';
    return new Intl.DateTimeFormat('en-GB', {
      ...(date.length === 7 ? {} : {day: 'numeric'}), month: 'short', year: 'numeric', timeZone: 'UTC'
    }).format(time) + (date.length === 7 ? ' (month only)' : '');
  };
  const periodText = record => dateText(dateOf(record)) + (record.end_date ? ` – ${dateText(record.end_date)}` : '');
  const resultText = record => record.value_as_reported || `${record.comparator || ''}${record.value} ${record.unit || ''}`.trim();
  const isPatientReport = record => record.evidence_type === 'patient_report_only';
  function titleOf(record) {
    if (record.title) return record.title;
    if (record.observation_id) return `${record.assay || 'ctDNA'} · ${resultText(record)}`;
    if (record.analyte) return `${record.series_label_as_reported || record.analyte} · ${resultText(record)}`;
    return `${record.modality || 'Imaging'}${record.region ? ` · ${record.region.replaceAll('_', ' ')}` : ''}`;
  }
  function statusOf(record) {
    if (isPatientReport(record)) return `Patient reported${record.result ? ` · ${human(record.result).replace(/ patient reported$/i, '')}` : ''}`;
    if (record.status || record.evidence_status) return human(record.status || record.evidence_status);
    if (record.result) return human(record.result);
    if (record.status_as_reported) return record.status_as_reported;
    if (record.evidence_type) return human(record.evidence_type);
    return 'Imaging report recorded';
  }
  const isPlan = record => /plan/.test(record.status || '');
  const isHold = record => /held|hold/i.test(record.title || '');
  const barLabels = {
    'EVT-006': 'Pelvic CRT', 'EVT-007': 'CAPOX · 6 cycles',
    'EVT-017': 'Abdominal SBRT', 'EVT-027': 'BOT / BAL'
  };

  window.drawUnifiedTimeline = ({timeline, imaging, ctdna, laboratory}) => {
    const host = document.getElementById('unified-timeline-content');
    const detail = document.getElementById('unified-timeline-detail');
    const period = document.getElementById('unified-period');
    const showCea = document.getElementById('unified-show-cea');
    if (!host || !detail || !period) return;
    const events = rows(timeline);
    const studies = rows(imaging);
    const dna = rows(ctdna).filter(record => (record.assay || 'Signatera') === 'Signatera');
    const cea = rows(laboratory).filter(record => /^(?:CEA(?:\s|\(|$)|Carcinoembryonic antigen)/i.test(record.analyte || '') && numeric(record));
    const plottedEvents = events.filter(record => ['systemic_therapy', 'radiotherapy', 'surgery', 'treatment_complication'].includes(record.category) && !/vaccine/i.test(record.title || ''));
    const allDated = [...plottedEvents, ...studies, ...dna, ...cea].flatMap(record => [timeOf(dateOf(record)), timeOf(record.end_date)]).filter(time => time !== null);
    if (!allDated.length) {
      host.replaceChildren(node('p', 'Dated records are not available in this release.'));
      return;
    }
    const fullStart = Date.UTC(2024, 2, 1);
    const fullEnd = Math.max(...allDated);
    const eventById = new Map(events.map(record => [recordId(record), record]));
    let selected = eventById.get('EVT-042') || plottedEvents.at(-1) || studies.at(-1);
    let chart;
    host.replaceChildren();

    function showDetail(record) {
      selected = record;
      detail.replaceChildren();
      const meta = node('div', undefined, 'unified-selected-meta');
      meta.append(node('span', `${recordId(record)} · ${periodText(record)}`), node('span', statusOf(record)));
      const summary = record.summary || record.notes || record.context || 'Select “Full record & sources” for the reported observation.';
      detail.append(meta, node('h4', titleOf(record)), node('p', summary));
      if (record.result && !record.title) detail.append(node('p', `Reported result: ${human(record.result)}${numeric(record) ? ` · ${resultText(record)}` : ''}.`));
      if (isPlan(record) && record.planned_start_date) detail.append(node('p', `Planned start: ${dateText(record.planned_start_date)}. The separately reported course retains its own record.`));
      if (record.date_precision === 'month') detail.append(node('p', 'The exact day is not recorded; the marker is placed at the middle of the reported month.'));
      detail.append(node('p', `Sources: ${sourceIds(record).join(', ') || 'Not recorded'}`, 'unified-source-ids'));
      const original = node('details', undefined, 'unified-record');
      original.append(node('summary', 'Full record & sources'), node('pre', JSON.stringify(record, null, 2)));
      detail.append(original);
      host.querySelectorAll('button[data-record-id]').forEach(button => {
        const active = button.dataset.recordId === recordId(record);
        button.classList.toggle('is-selected', active);
        button.setAttribute('aria-pressed', String(active));
      });
    }

    const stages = [
      ['EVT-006', 'Apr–May 2024', 'Pelvic chemoradiotherapy', 'Capecitabine + radiation'],
      ['EVT-007', 'Jun–Sep 2024', 'CAPOX', 'Six recorded cycles'],
      ['EVT-010', 'Oct 2024', 'Rectal + liver resection', 'Surgery on 22 October'],
      ['EVT-015', 'Jul 2025', 'Irinotecan + panitumumab', 'Start, then holds / restarts'],
      ['EVT-017', 'Sep–Oct 2025', 'Abdominal SBRT', 'Five reported fractions'],
      ['EVT-027', 'Jul–Sep 2026', 'Botensilimab + balstilimab', 'Two cycles, patient reported'],
      ['EVT-042', 'Oct 2026', 'Chemotherapy restart', 'Irinotecan + panitumumab + capecitabine']
    ];
    const strip = node('ol', undefined, 'unified-stage-strip');
    strip.setAttribute('aria-label', 'Treatment milestones');
    stages.forEach(([id, date, title, summary]) => {
      const record = eventById.get(id);
      if (!record) return;
      const item = node('li', undefined, 'unified-stage');
      const button = node('button');
      button.type = 'button';
      button.dataset.recordId = id;
      button.setAttribute('aria-label', `${date} · ${title}. Select ${id} for the recorded evidence.`);
      button.append(node('time', date), node('strong', title), node('span', summary));
      button.addEventListener('click', () => {
        if (period.value !== 'all' && period.value !== record.date?.slice(0, 4)) {
          period.value = record.date.slice(0, 4);
          renderChart();
        }
        showDetail(record);
      });
      item.append(button); strip.append(item);
    });
    const scroll = node('div', undefined, 'unified-chart-scroll');
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', 'Unified treatment, imaging and biomarker timeline. Scroll horizontally on smaller screens.');
    host.append(strip, scroll);

    const series = new Map();
    cea.forEach(record => {
      // Do not combine portal series, even when their displayed assay names match.
      const key = record.series_id || `${record.series_label_as_reported || record.analyte}|${record.assay_method_as_reported || record.assay_method || 'method unconfirmed'}|${record.unit}`;
      if (!series.has(key)) series.set(key, []);
      series.get(key).push(record);
    });
    const datedDna = dna.filter(record => timeOf(dateOf(record)) !== null && numeric(record));
    // All periods share a fixed scale derived from the complete dated series.
    // Multiples of 100 keep the four equal intervals numerically readable.
    const dnaMaximum = Math.max(100, Math.ceil(Math.max(0, ...datedDna.map(record => record.value)) / 100) * 100);

    function renderChart() {
      const year = /^202[456]$/.test(period.value) ? Number(period.value) : null;
      const start = year ? Math.max(fullStart, Date.UTC(year, 0, 1)) : fullStart;
      const end = year ? Math.min(fullEnd, Date.UTC(year, 11, 31)) : fullEnd;
      const span = Math.max(1, end - start);
      // Inset endpoints leave room for the complete keyboard-focusable markers.
      const position = time => 2.5 + 95 * (time - start) / span;
      const visible = record => {
        const time = timeOf(dateOf(record));
        const endTime = timeOf(record.end_date) ?? time;
        return time !== null && time <= end && endTime >= start;
      };
      if (selected && timeOf(dateOf(selected)) !== null && !visible(selected)) {
        selected = plottedEvents.filter(visible).sort((a, b) => timeOf(dateOf(a)) - timeOf(dateOf(b))).at(-1)
          || studies.filter(visible).at(-1) || selected;
      }
      chart = node('div', undefined, 'unified-chart');
      chart.dataset.period = year || 'all';
      scroll.replaceChildren(chart);
      const ticks = [];
      const firstTick = new Date(start);
      if (!year) {
        ticks.push(start);
        for (let tickYear = firstTick.getUTCFullYear(); tickYear <= new Date(end).getUTCFullYear(); tickYear += 1) {
          for (const month of [0, 6]) {
            const time = Date.UTC(tickYear, month, 1);
            if (time > start && time < end - 35 * 86400000) ticks.push(time);
          }
        }
      } else {
        for (let month = firstTick.getUTCMonth(); month < 12; month += 1) {
          const time = Date.UTC(year, month, 1);
          if (time >= start && time < end - 18 * 86400000) ticks.push(time);
        }
      }
      ticks.push(end);
      const axis = node('div', undefined, 'unified-axis');
      axis.append(node('div', year ? String(year) : 'Mar 2024–Oct 2026', 'unified-lane-label'));
      const axisTrack = node('div', undefined, 'unified-track');
      ticks.forEach((time, index) => {
        const endpoint = index === ticks.length - 1;
        const label = new Intl.DateTimeFormat('en-GB', {
          ...(endpoint ? {day: 'numeric'} : {}), month: 'short',
          ...(year ? {} : {year: 'numeric'}), timeZone: 'UTC'
        }).format(time);
        const tick = node('span', label, 'unified-tick');
        tick.style.left = `${position(time)}%`;
        if (index === 0) tick.style.transform = 'translateX(0)';
        if (index === ticks.length - 1) tick.style.transform = 'translateX(-100%)';
        tick.title = dateText(new Date(time).toISOString().slice(0, 10));
        axisTrack.append(tick);
      });
      axis.append(axisTrack); chart.append(axis);

      function lane(title, subtitle, kind, height = 66) {
        const row = node('div', undefined, `unified-lane kind-${kind}`);
        const label = node('div', undefined, 'unified-lane-label');
        label.append(node('strong', title), node('small', subtitle));
        const track = node('div', undefined, 'unified-track');
        track.style.minHeight = `${height}px`;
        ticks.forEach(time => {
          const line = node('span', undefined, 'unified-gridline');
          line.setAttribute('aria-hidden', 'true');
          line.style.left = `${position(time)}%`;
          track.append(line);
        });
        row.append(label, track); chart.append(row);
        return track;
      }

      function marker(track, record, kind, top, label = '', range = false) {
        const time = timeOf(dateOf(record));
        const button = node('button', undefined, `unified-marker kind-${kind}${range ? ' unified-bar' : ''}${isPlan(record) ? ' is-plan' : ''}${isHold(record) ? ' is-hold' : ''}${record.comparator ? ' is-bound' : ''}${isPatientReport(record) ? ' is-patient-report' : ''}`);
        button.type = 'button';
        button.dataset.recordId = recordId(record);
        button.style.left = `${position(Math.max(start, time))}%`;
        button.style.top = `${top}px`;
        if (range) button.style.width = `${position(Math.min(end, timeOf(record.end_date))) - position(Math.max(start, time))}%`;
        const description = `${periodText(record)} · ${titleOf(record)} · ${recordId(record)} · ${statusOf(record)}${range ? (kind === 'hospital' ? ' · recorded admission and discharge dates' : ' · recorded date range; individual dosing may be intermittent') : ''}`;
        button.title = description;
        button.setAttribute('aria-label', description);
        button.setAttribute('aria-pressed', String(recordId(record) === recordId(selected)));
        button.classList.toggle('is-selected', recordId(record) === recordId(selected));
        if (label) button.append(node('span', label, 'unified-marker-label'));
        button.addEventListener('click', () => showDetail(record));
        track.append(button);
      }

      function treatmentLane(category, title, subtitle, kind, height) {
        const track = lane(title, subtitle, kind, height);
        const lastOccupied = [-Infinity, -Infinity, -Infinity];
        const records = plottedEvents.filter(record => record.category === category && visible(record)).sort((a, b) => timeOf(dateOf(a)) - timeOf(dateOf(b)));
        records.forEach(record => {
          const left = position(Math.max(start, timeOf(dateOf(record))));
          const row = lastOccupied.findIndex(value => left > value);
          const slot = row === -1 ? lastOccupied.indexOf(Math.min(...lastOccupied)) : row;
          const range = !!record.end_date && timeOf(record.end_date) > timeOf(dateOf(record)) && !isPlan(record);
          const right = range ? position(Math.min(end, timeOf(record.end_date))) : left;
          lastOccupied[slot] = right + 3;
          const label = barLabels[recordId(record)] || (kind === 'hospital' ? 'Ulcer admission' : record.title);
          marker(track, record, kind, 16 + slot * 27, range || kind === 'hospital' ? label : '', range);
          track.style.minHeight = `${Math.max(height, parseFloat(track.style.minHeight), 43 + slot * 27)}px`;
        });
        if (!records.length) track.append(node('span', 'No recorded events in this period', 'unified-empty-lane'));
      }
      treatmentLane('systemic_therapy', 'Systemic therapy', 'Starts, doses, holds and plans', 'systemic', 100);
      treatmentLane('radiotherapy', 'Radiotherapy', 'Recorded course ranges', 'radiotherapy', 66);
      treatmentLane('surgery', 'Surgery', 'Resection and reversal', 'surgery', 66);
      treatmentLane('treatment_complication', 'Ulcer / admissions', 'Recorded hospital stays', 'hospital', 66);
      const imagingTrack = lane('Imaging', 'CT · MRI · FDG PET/CT', 'imaging', 108);
      const lastImaging = [-Infinity, -Infinity, -Infinity, -Infinity];
      studies.filter(visible).sort((a, b) => timeOf(dateOf(a)) - timeOf(dateOf(b))).forEach(record => {
        const left = position(timeOf(dateOf(record)));
        const free = lastImaging.findIndex(value => left > value);
        const slot = free === -1 ? lastImaging.indexOf(Math.min(...lastImaging)) : free;
        lastImaging[slot] = left + 3;
        marker(imagingTrack, record, 'imaging', 15 + slot * 23);
      });

      function biomarkerLane(records, title, subtitle, kind, maximum, options = {}) {
        const height = options.height || 100;
        const track = lane(title, subtitle, kind, height);
        const measurements = records.filter(record => visible(record) && numeric(record)).sort((a, b) => timeOf(dateOf(a)) - timeOf(dateOf(b)));
        const y = value => (options.top ?? 19) + (options.range ?? 63) * (1 - value / maximum);
        if (options.yAxis) {
          const label = chart.lastElementChild.querySelector('.unified-lane-label');
          label.classList.toggle('has-y-axis', true);
          const axis = node('div', undefined, 'unified-y-axis');
          axis.setAttribute('role', 'img');
          const values = Array.from({length: 5}, (_, index) => maximum * index / 4);
          axis.setAttribute('aria-label', `Linear y-axis: ${values.join(', ')} ${options.unit || ''}`);
          values.forEach(value => {
            const tick = node('span', String(value), 'unified-y-tick');
            tick.style.top = `${y(value)}px`;
            const gridline = node('span', undefined, 'unified-y-gridline');
            gridline.style.top = `${y(value)}px`;
            gridline.setAttribute('aria-hidden', 'true');
            axis.append(tick); track.append(gridline);
          });
          label.append(axis);
        }
        if (measurements.length > 1) {
          const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          svg.setAttribute('viewBox', `0 0 1000 ${height}`);
          svg.setAttribute('preserveAspectRatio', 'none');
          svg.setAttribute('aria-hidden', 'true');
          svg.setAttribute('focusable', 'false');
          svg.setAttribute('class', `unified-plot kind-${kind}`);
          const segments = [[]];
          measurements.forEach(record => {
            // Patient-only observations retain their own provenance and do not
            // extend the line joining primary-report measurements.
            if (record.comparator || isPatientReport(record)) segments.push([]);
            else segments.at(-1).push(record);
          });
          segments.filter(segment => segment.length > 1).forEach(segment => {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            line.setAttribute('points', segment.map(record => `${position(timeOf(dateOf(record))) * 10},${y(record.value)}`).join(' '));
            line.setAttribute('fill', 'none');
            line.setAttribute('stroke', 'currentColor');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('vector-effect', 'non-scaling-stroke');
            line.setAttribute('class', 'unified-trend-line');
            svg.append(line);
          });
          if (svg.childElementCount) track.append(svg);
        }
        measurements.forEach(record => marker(track, record, kind, y(record.value) - 8, record.comparator ? resultText(record) : ''));
        if (!measurements.length) track.append(node('span', 'No measurements in this period', 'unified-empty-lane'));
      }
      biomarkerLane(datedDna, 'Signatera ctDNA', 'MTM/mL · linear', 'ctdna', dnaMaximum, {
        height: 160, top: 27, range: 104, yAxis: true, unit: 'MTM/mL'
      });
      let labdaqIndex = 0;
      if (!showCea || showCea.checked) [...series.entries()].forEach(([id, records]) => {
        const assay = records[0].series_label_as_reported || records[0].analyte;
        const labdaq = /LabDAQ/i.test(assay);
        if (labdaq) labdaqIndex += 1;
        const name = labdaq ? `${assay} · series ${labdaqIndex}` : /Carcinoembryonic/i.test(assay) ? 'CEA · City of Hope' : assay;
        const reportedMethod = records[0].assay_method_as_reported || records[0].assay_method || '';
        const method = /Roche cobas e801/.test(reportedMethod) ? 'Roche cobas e801' : 'Method unconfirmed';
        const maximum = Math.max(1, ...records.filter(record => timeOf(dateOf(record)) !== null).map(record => record.value));
        const scale = records.every(record => record.comparator) ? `${resultText(records[0])} · reported bound` : `0–${maximum} ${records[0].unit || ''} · linear`;
        biomarkerLane(records, name, `${method} · ${scale}`, 'cea', maximum);
        chart.lastElementChild.querySelector('.unified-lane-label').title = `${assay} · ${id} · ${records[0].assay_method_as_reported || records[0].assay_method || 'Assay method not supplied'}`;
      });
    }

    const undated = dna.filter(record => timeOf(dateOf(record)) === null);
    if (undated.length) {
      const note = node('div', undefined, 'unified-undated');
      note.append(node('span', 'Date not supplied · '));
      undated.forEach(record => {
        const button = node('button', `${record.assay} ${resultText(record)} (${recordId(record)})`, 'unified-undated-button');
        button.type = 'button'; button.dataset.recordId = recordId(record);
        button.title = 'Patient reported value; exact draw date and original report unavailable. Not plotted on the time axis.';
        button.addEventListener('click', () => showDetail(record));
        note.append(button);
      });
      note.append(node('span', ' · Patient reported; excluded from the dated trend.'));
      host.append(note);
    }
    const notes = node('p', 'Treatment bars show recorded start/end ranges, not uninterrupted dosing; admission bars use recorded admission/discharge dates. Points include holds and separate plans. Trend lines join available samples. Signatera uses one linear scale across all years; patient-reported results are separate hollow squares, without a connecting line to primary-report measurements. CEA source series remain separate; assays are not interchangeable. Month-only events are positioned mid-month.', 'unified-footnotes');
    host.append(notes);
    period.onchange = () => { renderChart(); showDetail(selected); };
    if (showCea) showCea.onchange = () => {
      if (!showCea.checked && cea.includes(selected)) selected = eventById.get('EVT-042') || plottedEvents.at(-1);
      renderChart(); showDetail(selected);
    };
    renderChart(); showDetail(selected);
  };
})();
