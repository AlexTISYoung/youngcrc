export const researchTools = [
  {name: 'search_reports', description: 'Find public provider reports and their pertinent results, source IDs and limitations.', inputSchema: {type: 'object', properties: {query: {type: 'string', maxLength: 200}, provider_id: {type: 'string', maxLength: 100}, type: {type: 'string', maxLength: 100}, offset: {type: 'integer', minimum: 0}, limit: {type: 'integer', minimum: 1, maximum: 50}}, additionalProperties: false}},
  {name: 'search_catalogue', description: 'Find released datasets by modality, subtype and provider, including provenance and availability.', inputSchema: {type: 'object', properties: {query: {type: 'string', maxLength: 200}, modality: {type: 'string', maxLength: 100}, provider_id: {type: 'string', maxLength: 100}, offset: {type: 'integer', minimum: 0}, limit: {type: 'integer', minimum: 1, maximum: 50}}, additionalProperties: false}},
  {name: 'get_public_dataset', description: 'Read a bounded page of a published JSON dataset. Use path from the catalogue or /agents/datasets.json; retain source IDs and document metadata.', inputSchema: {type: 'object', required: ['path'], properties: {path: {type: 'string', maxLength: 200}, offset: {type: 'integer', minimum: 0}, limit: {type: 'integer', minimum: 1, maximum: 100}}, additionalProperties: false}}
].map(tool => ({...tool, annotations: {readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false}}));

function validate(tool, args) {
  if (!args || typeof args !== 'object' || Array.isArray(args)) throw new Error('Arguments must be an object.');
  const schema = tool.inputSchema;
  for (const required of schema.required || []) if (!(required in args)) throw new Error('Missing ' + required + '.');
  for (const [key, value] of Object.entries(args)) {
    const rule = schema.properties[key];
    if (!rule) throw new Error('Unknown argument: ' + key + '.');
    if (rule.type === 'string' && (typeof value !== 'string' || value.length > rule.maxLength)) throw new Error('Invalid ' + key + '.');
    if (rule.type === 'integer' && (!Number.isInteger(value) || value < rule.minimum || (rule.maximum && value > rule.maximum))) throw new Error('Invalid ' + key + '.');
  }
}

export async function executeResearchTool(name, args = {}, load, allowedPaths) {
  const tool = researchTools.find(t => t.name === name);
  if (!tool) throw new Error('Unknown tool.');
  validate(tool, args);
  const origin = 'https://youngcrc.com';
  let path;
  if (name === 'search_reports') path = '/data/reports.json';
  else if (name === 'search_catalogue') path = '/data/catalogue.json';
  else path = args.path.startsWith('/') ? args.path : '/' + args.path;
  if (!allowedPaths.includes(path)) throw new Error('Only published dataset paths from /agents/datasets.json are supported.');
  const doc = await load(path);
  let records = Array.isArray(doc) ? doc : Array.isArray(doc.records) ? doc.records : null;
  if (!records) {
    if (JSON.stringify(doc).length > 32768) return {url: origin + path, note: 'This structured document is large and has no records array. Retrieve the full public URL for its original schema.'};
    return {url: origin + path, document: doc};
  }
  const metadata = Array.isArray(doc) ? {} : Object.fromEntries(Object.entries(doc).filter(([key]) => key !== 'records'));
  if (name !== 'get_public_dataset') {
    const query = (args.query || '').toLowerCase();
    records = records.filter(r => (!args.provider_id || r.provider_id === args.provider_id) && (!args.modality || r.browse_modality === args.modality) && (!args.type || r.browse_type === args.type) && JSON.stringify(r).toLowerCase().includes(query));
  }
  const offset = args.offset || 0;
  const limit = args.limit || 20;
  return {url: origin + path, metadata, total: records.length, offset, limit, next_offset: offset + limit < records.length ? offset + limit : null, records: records.slice(offset, offset + limit)};
}

if (typeof document !== 'undefined') {
  const modelContext = document.modelContext || navigator.modelContext;
  if (modelContext && typeof modelContext.registerTool === 'function') {
    const controller = new AbortController();
    const paths = fetch('/agents/datasets.json').then(r => {if (!r.ok) throw new Error('Dataset discovery is unavailable.'); return r.json();}).then(d => d.paths);
    const load = async (path, signal) => {
      const response = await fetch(path, {signal});
      if (!response.ok) throw new Error('Dataset is unavailable.');
      return response.json();
    };
    for (const tool of researchTools) {
      Promise.resolve(modelContext.registerTool({...tool, execute: async (args, client) => executeResearchTool(tool.name, args, path => load(path, client?.signal), await paths)}, {signal: controller.signal})).catch(error => console.warn('Research tool registration failed:', error.message));
    }
    window.addEventListener('pagehide', event => { if (!event.persisted) controller.abort(); });
  }
}
