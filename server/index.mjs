import {publicContent, datasetPaths} from './public-content.mjs';
import {researchTools, executeResearchTool} from './agent-tools.mjs';

const origin = 'https://youngcrc.com';
const version = '2025-11-25';
const signals = 'search=yes, ai-input=yes, ai-train=yes';
const links = '</.well-known/api-catalog>; rel="api-catalog", </openapi.json>; rel="service-desc"; type="application/json", </docs/api.md>; rel="service-doc"; type="text/markdown", </.well-known/ard.json>; rel="describedby"; type="application/json", </agents/case.md>; rel="alternate"; type="text/markdown"';
const browserOrigins = new Set([origin, 'https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site', 'https://chatgpt.com', 'https://claude.ai', 'https://www.perplexity.ai']);

function headers(type) {
  return {'Content-Type': type, 'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'Link, Content-Signal, MCP-Protocol-Version', 'X-Content-Type-Options': 'nosniff', 'Content-Signal': signals, 'Link': links};
}
function response(body, type, status = 200, extra = {}) {
  return new Response(body, {status, headers: {...headers(type), ...extra}});
}
function json(body, status = 200, extra = {}) {
  return response(JSON.stringify(body), 'application/json; charset=utf-8', status, extra);
}
function quality(accept, type) {
  for (const item of accept.toLowerCase().split(',')) {
    const [media, ...params] = item.trim().split(';');
    if (media.trim() !== type) continue;
    const q = params.find(p => p.trim().startsWith('q='));
    const value = q ? Number(q.trim().slice(2)) : 1;
    return Number.isFinite(value) && value >= 0 && value <= 1 ? value : 0;
  }
  return 0;
}

async function mcp(request) {
  const requestOrigin = request.headers.get('Origin');
  if (requestOrigin && !browserOrigins.has(requestOrigin)) return json({error: 'Origin is not allowed.'}, 403);
  const mcpVersion = request.headers.get('MCP-Protocol-Version');
  if (mcpVersion && mcpVersion !== version) return json({error: 'Unsupported MCP protocol version.'}, 400);
  if (request.method === 'OPTIONS') return response(null, 'application/json', 204, {'Access-Control-Allow-Methods': 'POST, GET, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, MCP-Protocol-Version', 'Access-Control-Max-Age': '600'});
  if (request.method !== 'POST') return response('This stateless endpoint accepts POST; it does not offer an SSE stream.', 'text/plain; charset=utf-8', 405, {Allow: 'POST, OPTIONS'});
  if (!(request.headers.get('Content-Type') || '').toLowerCase().startsWith('application/json')) return json({error: 'Use application/json.'}, 415);
  const accept = request.headers.get('Accept') || '';
  if (quality(accept, 'application/json') === 0 || quality(accept, 'text/event-stream') === 0) return json({error: 'Accept must include application/json and text/event-stream.'}, 406);
  const body = await request.text();
  if (body.length > 65536) return json({error: 'Request too large.'}, 413);
  let message;
  try { message = JSON.parse(body); } catch { return json({jsonrpc: '2.0', id: null, error: {code: -32700, message: 'Parse error'}}, 400); }
  if (!message || Array.isArray(message) || message.jsonrpc !== '2.0' || typeof message.method !== 'string') return json({jsonrpc: '2.0', id: null, error: {code: -32600, message: 'Invalid Request'}}, 400);
  const id = message.id;
  if (!Object.hasOwn(message, 'id')) return response(null, 'application/json', 202);
  if (!(typeof id === 'string' || (typeof id === 'number' && Number.isFinite(id)))) return json({jsonrpc: '2.0', id: null, error: {code: -32600, message: 'Invalid request ID'}}, 400);
  const result = value => json({jsonrpc: '2.0', id, result: value}, 200, {'MCP-Protocol-Version': version, 'Cache-Control': 'no-store'});
  const error = (code, text) => json({jsonrpc: '2.0', id, error: {code, message: text}}, 200, {'Cache-Control': 'no-store'});
  if (message.method === 'initialize') return result({protocolVersion: version, capabilities: {tools: {}}, serverInfo: {name: 'com.youngcrc/research-data', version: '1.0.0'}, instructions: 'Public research data. Preserve evidence status, source/specimen linkage and limitations. Data are not treatment advice.'});
  if (message.method === 'ping') return result({});
  if (message.method === 'tools/list') return result({tools: researchTools});
  if (message.method === 'tools/call') {
    if (!message.params || typeof message.params.name !== 'string') return error(-32602, 'Tool name is required.');
    try {
      const value = await executeResearchTool(message.params.name, message.params.arguments || {}, async path => JSON.parse(publicContent[path].body), datasetPaths);
      return result({content: [{type: 'text', text: JSON.stringify(value)}], structuredContent: value});
    } catch (e) { return error(-32602, e.message); }
  }
  return error(-32601, 'Method not found');
}

export default {
  async fetch(request, env, ctx) {
    void ctx;
    const path = new URL(request.url).pathname;
    if (path === '/mcp') return mcp(request);
    if (request.method === 'OPTIONS') return response(null, 'text/plain', 204, {'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, If-None-Match', 'Access-Control-Max-Age': '600'});
    if (!['GET', 'HEAD'].includes(request.method)) return response('Method not allowed', 'text/plain', 405, {Allow: 'GET, HEAD, OPTIONS'});
    // MCP lives at the native Sites origin. Keep its resource metadata authoritative there.
    if (path === '/.well-known/oauth-protected-resource') return response(null, 'text/plain; charset=utf-8', 302, {Location: 'https://alexander-young-open-cancer-data.alextisyoung.chatgpt.site/.well-known/oauth-protected-resource/mcp', 'Cache-Control': 'public, max-age=300'});
    let key = path;
    const extra = {'Cache-Control': 'public, max-age=300'};
    if (path === '/' || path === '/index.html') {
      const accept = request.headers.get('Accept') || '';
      key = quality(accept, 'text/markdown') > 0 && quality(accept, 'text/markdown') >= quality(accept, 'text/html') ? '/agents/case.md' : '/index.html';
      extra.Vary = 'Accept';
    }
    const file = publicContent[key];
    if (file) return response(request.method === 'HEAD' ? null : file.body, file.type, 200, extra);
    if (env.ASSETS?.fetch) {
      const asset = await env.ASSETS.fetch(request);
      const out = new Response(asset.body, asset);
      for (const [name, value] of Object.entries(headers(asset.headers.get('Content-Type') || 'application/octet-stream'))) out.headers.set(name, value);
      return out;
    }
    return response('Not found', 'text/plain; charset=utf-8', 404);
  }
};
