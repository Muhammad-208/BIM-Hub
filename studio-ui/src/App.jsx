import React, { useEffect, useState } from 'react'
import { api } from './api.js'
import Projects from './pages/Projects.jsx'
import Studio from './pages/Studio.jsx'
import Settings from './pages/Settings.jsx'

export default function App() {
  const [page, setPage] = useState('studio')
  const [projects, setProjects] = useState([])
  const [code, setCode] = useState(() => { try { return localStorage.getItem('bimhub.project') || '' } catch { return '' } })
  const [auth, setAuth] = useState(null)
  const [error, setError] = useState('')

  const loadProjects = () => api.projects().then((ps) => {
    setProjects(ps); setError('')
    if (!ps.find((p) => p.code === code) && ps[0]) setCode(ps[0].code)
    if (!ps.length) setPage('projects')
  })

  useEffect(() => {
    // the desktop shell starts the backend at the same time as the window: retry for ~20 s
    let tries = 0, stop = false
    const attempt = () => loadProjects().then(() => api.auth().then(setAuth).catch(() => {})).catch((e) => {
      if (stop) return
      if (++tries < 20) setTimeout(attempt, 1000)
      else setError('Studio API not reachable: ' + e.message)
    })
    attempt()
    return () => { stop = true }
  }, [])
  useEffect(() => { try { localStorage.setItem('bimhub.project', code) } catch { /* private mode */ } }, [code])

  const authOk = auth && auth.installed && (auth.mode === 'api_key' ? auth.api_key_set : auth.loggedIn !== false)
  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true"><path d="M13 2 23 8v10l-10 6L3 18V8z" stroke="#F2A541" strokeWidth="1.6" /><path d="M13 2v10m0 0 10-4M13 12 3 8m10 4v12" stroke="#F2A541" strokeWidth="1.2" opacity=".6" /></svg>
          BIM Hub <span className="mute" style={{ fontWeight: 400 }}>Studio</span>
        </div>
        <nav className="nav" aria-label="Main">
          {[['projects', 'Projects'], ['studio', 'Studio 3D'], ['settings', 'Settings']].map(([k, l]) =>
            <button key={k} className={page === k ? 'on' : ''} aria-current={page === k ? 'page' : undefined} onClick={() => setPage(k)}>{l}</button>)}
        </nav>
        <label className="pill mute">Project
          <select className="input" style={{ width: 'auto', minHeight: 34, padding: '4px 8px' }} value={code} onChange={(e) => setCode(e.target.value)}>
            {projects.map((p) => <option key={p.code} value={p.code}>{p.code} — {p.name}</option>)}
          </select>
        </label>
        <div className="grow" />
        <button className="pill mono" style={{ background: 'transparent', border: 0, color: 'var(--mute)' }} onClick={() => setPage('settings')}
          title="Claude connection">
          <span className="dot" style={{ background: authOk ? 'var(--green)' : 'var(--red)' }} />
          {auth ? (auth.mode === 'api_key' ? 'API key' : 'Claude subscription') + (auth.version ? ' · ' + auth.version.split(' ')[0] : '') : 'checking Claude…'}
        </button>
      </header>
      {error && <div className="note err" style={{ margin: 12 }}>{error} — start it with <span className="mono">.\bimhub.cmd studio</span></div>}
      {page === 'projects' && <Projects projects={projects} current={code} onPick={(c) => { setCode(c); setPage('studio') }} reload={loadProjects} />}
      {page === 'studio' && code && <Studio code={code} key={code} />}
      {page === 'studio' && !code && <div className="page"><div className="note">Create a project first.</div></div>}
      {page === 'settings' && <Settings auth={auth} onChange={() => api.auth().then(setAuth)} />}
    </div>
  )
}
