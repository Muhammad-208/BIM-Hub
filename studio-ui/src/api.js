// Same origin when served by `bimhub studio`; absolute when loaded inside the Tauri shell.
const inTauri = location.protocol === 'tauri:' || location.hostname === 'tauri.localhost'
export const BASE = inTauri ? 'http://127.0.0.1:8800' : ''

async function req(method, path, body) {
  const r = await fetch(BASE + path, {
    method, headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.error || r.statusText)
  return data
}

export const api = {
  health: () => req('GET', '/api/health'),
  auth: () => req('GET', '/api/auth'),
  settings: () => req('GET', '/api/settings'),
  saveSettings: (s) => req('PUT', '/api/settings', s),
  setKey: (key) => req('PUT', '/api/settings/api-key', { key }),
  projects: () => req('GET', '/api/projects'),
  projectTypes: () => req('GET', '/api/project-types'),
  createProject: (p) => req('POST', '/api/projects', p),
  project: (c) => req('GET', `/api/projects/${c}`),
  state: (c) => req('GET', `/api/projects/${c}/state`),
  files: (c, q = {}) => req('GET', `/api/projects/${c}/files?` + new URLSearchParams(Object.entries(q).filter(([, v]) => v))),
  scan: (c) => req('POST', `/api/projects/${c}/scan`),
  addSource: (c, s) => req('POST', `/api/projects/${c}/sources`, s),
  chat: (c, agent, text, context) => req('POST', `/api/projects/${c}/chat`, { agent, text, context }),
  resetAgent: (c, a) => req('POST', `/api/projects/${c}/agents/${a}/reset`),
  approveLesson: (c, id) => req('POST', `/api/projects/${c}/lessons/${id}/approve`),
  dashboardUrl: (c, kind) => `${BASE}/api/projects/${c}/dashboards/${kind}`,
  events: (c) => new EventSource(`${BASE}/api/projects/${c}/events`)
}

export const LAYER = {
  4: { label: 'L4 · Management', color: '#F2A541' },
  3: { label: 'L3 · Coordination', color: '#A78BFA' },
  2: { label: 'L2 · QA / QC', color: '#2DD4BF' },
  1: { label: 'L1 · Discipline teams', color: '#60A5FA' }
}
export const ROLE_SHORT = { leader: 'LEAD', modeler: 'MOD', drafter: 'DRF', clash: 'CLS', info: 'INF' }
export const agentColor = (a) => !a ? '#93A0B0' : a.layer === 1 && a.role !== 'leader' ? '#9CC7FF' : LAYER[a.layer].color
export const hhmm = (iso) => (iso || '').slice(11, 19)
