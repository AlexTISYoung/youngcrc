/* Public display controls. Scores and plots are read from the published data. */
(() => {
  'use strict';

  const plot = document.getElementById('plot-scatter');
  const tierControl = document.getElementById('tierFilter');
  const markerControl = document.getElementById('scaleToggle');
  const expandControl = document.getElementById('showCandidates');
  let figureRequest;
  let drawVersion = 0;
  let simpleMarkers = false;

  function currentTable() {
    return document.querySelector('.cand-table:not([hidden]) table');
  }

  function refreshTableLayout() {
    document.documentElement.style.setProperty('--vw', `${document.documentElement.clientWidth}px`);
    document.querySelectorAll('.table-scroll').forEach(wrapper => {
      wrapper.classList.toggle('scrolls', wrapper.scrollWidth > wrapper.clientWidth);
    });
  }

  function orderRows(table, column, direction) {
    const headers = Array.from(table.tHead.rows[0].cells);
    const header = headers[column];
    const numeric = header.dataset.type === 'num';
    const rows = Array.from(table.tBodies[0].rows);
    const value = row => row.cells[column].dataset.sort ?? row.cells[column].textContent.trim();
    rows.sort((left, right) => {
      const a = value(left), b = value(right);
      if (a === '' || b === '') return a === b ? 0 : a === '' ? 1 : -1;
      const comparison = numeric ? Number(a) - Number(b) : a.localeCompare(b, undefined, {numeric: true});
      return direction === 'ascending' ? comparison : -comparison;
    });
    headers.forEach(cell => cell.removeAttribute('aria-sort'));
    header.setAttribute('aria-sort', direction);
    rows.forEach(row => table.tBodies[0].append(row));
  }

  document.querySelectorAll('table.data').forEach(table => {
    table.closest('.card').classList.add('has-table');
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('aria-label', 'Scrollable candidate table');
    table.before(wrapper);
    wrapper.append(table);
    Array.from(table.tHead.rows[0].cells).forEach((header, column) => {
      if (!header.classList.contains('sortable')) return;
      header.tabIndex = 0;
      const sort = () => {
        const prior = header.getAttribute('aria-sort');
        const direction = prior ? (prior === 'ascending' ? 'descending' : 'ascending')
          : (header.dataset.first === 'desc' ? 'descending' : 'ascending');
        orderRows(table, column, direction);
      };
      header.addEventListener('click', sort);
      header.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); sort(); }
      });
    });
  });

  expandControl.addEventListener('click', () => {
    const table = currentTable();
    const rankColumn = Array.from(table.tHead.rows[0].cells).findIndex(cell => cell.classList.contains('rank-col'));
    orderRows(table, rankColumn, 'ascending');
    const expanded = table.classList.toggle('show-all');
    expandControl.textContent = expanded ? expandControl.dataset.less : expandControl.dataset.more;
    expandControl.setAttribute('aria-expanded', String(expanded));
    refreshTableLayout();
  });

  document.getElementById('csvDownloadBtn').addEventListener('click', () => {
    const table = currentTable();
    const columns = Array.from(table.tHead.rows[0].cells)
      .map((cell, index) => cell.hasAttribute('data-noexport') ? null : index)
      .filter(index => index !== null);
    const cellText = cell => {
      const copy = cell.cloneNode(true);
      copy.querySelectorAll('.sort-arr, .dropped-flag').forEach(node => node.remove());
      return copy.textContent.replace(/\s+/g, ' ').trim();
    };
    const rows = [table.tHead.rows[0], ...Array.from(table.tBodies[0].rows)
      .filter(row => getComputedStyle(row).display !== 'none')];
    const csv = rows.map(row => columns.map(column => `"${cellText(row.cells[column]).replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'vaccine_candidates_2026-09-28.csv';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });

  function retainPoints(value, positions, count) {
    if (Array.isArray(value)) return value.length === count ? positions.map(index => value[index]) : value;
    if (value && typeof value === 'object') {
      return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, retainPoints(item, positions, count)]));
    }
    return value;
  }

  async function drawScatter() {
    const requestVersion = ++drawVersion;
    try {
      if (!figureRequest) {
        figureRequest = fetch('./figure_data.json', {credentials: 'omit'})
          .then(response => { if (!response.ok) throw new Error('Figure data unavailable'); return response.json(); })
          .catch(error => { figureRequest = undefined; throw error; });
      }
      const figures = await figureRequest;
      if (requestVersion !== drawVersion || !document.getElementById('scatter').classList.contains('active')) return;
      const figure = JSON.parse(JSON.stringify(figures.scatter));
      const maximumTier = Number(tierControl.value);
      const allowedCoordinates = new Set();
      figure.data = figure.data.map(trace => {
        if (!trace.customdata || !trace.mode?.includes('markers')) return trace;
        const positions = trace.customdata.flatMap((record, index) => Number(record[6]) <= maximumTier ? [index] : []);
        const filtered = retainPoints(trace, positions, trace.customdata.length);
        filtered.x.forEach((x, index) => allowedCoordinates.add(`${x}:${filtered.y[index]}`));
        filtered.name = `Candidates (n=${positions.length})`;
        if (simpleMarkers) {
          filtered.marker.size = 9;
          filtered.marker.color = '#1C3C5A';
          filtered.marker.showscale = false;
        }
        return filtered;
      });
      figure.data = figure.data.map(trace => {
        if (trace.mode !== 'text' || maximumTier === 4) return trace;
        const positions = trace.x.flatMap((x, index) => allowedCoordinates.has(`${x}:${trace.y[index]}`) ? [index] : []);
        return retainPoints(trace, positions, trace.x.length);
      });
      figure.layout.autosize = true;
      figure.layout.uirevision = 'public-scatter';
      await Plotly.react(plot, figure.data, figure.layout, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
      });
      document.getElementById('plot-status').textContent = '';
    } catch (error) {
      document.getElementById('plot-status').textContent = 'The scatter could not load. Reload this page to try again.';
      console.error('Public scatter display failed:', error);
    }
  }

  tierControl.addEventListener('change', drawScatter);
  markerControl.addEventListener('click', () => {
    simpleMarkers = !simpleMarkers;
    markerControl.textContent = simpleMarkers ? 'Use expression / DNA AF markers' : 'Simplify markers';
    markerControl.setAttribute('aria-pressed', String(simpleMarkers));
    drawScatter();
  });

  function displayView() {
    const requested = location.hash.slice(1);
    const id = ['home', 'scatter', 'candidates'].includes(requested) ? requested : 'home';
    document.querySelectorAll('section.view').forEach(section => section.classList.toggle('active', section.id === id));
    document.querySelectorAll('nav a[data-view]').forEach(link => {
      const selected = link.dataset.view === id;
      link.classList.toggle('active', selected);
      if (selected) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
    if (id === 'scatter') drawScatter();
    refreshTableLayout();
    window.scrollTo(0, 0);
  }

  document.querySelectorAll('[data-tip]').forEach(element => {
    if (!element.hasAttribute('title')) element.setAttribute('title', element.dataset.tip);
  });
  window.addEventListener('hashchange', displayView);
  window.addEventListener('resize', refreshTableLayout);
  displayView();
})();
