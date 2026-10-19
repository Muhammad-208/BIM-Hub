import React, { useEffect, useState } from 'react'
import { api } from '../api.js'

const DISCS = ['arc', 'str', 'mech', 'plumb', 'ff', 'elec', 'ict', 'infra', 'land']
const KINDS = [['', 'All'], ['point-cloud', 'Point cloud'], ['revit-model', 'RVT'], ['ifc', 'IFC'], ['navisworks-cache', 'NWC'], ['navisworks-fileset', 'NWF'],
  ['navisworks-document', 'NWD'], ['dwg', 'DWG'], ['word', 'DOCX'], ['excel', 'XLSX'], ['pdf', 'PDF'], ['text', 'TXT'], ['csv', 'CSV']]
const CONTENT = new Set(['ifc', 'word', 'excel', 'pdf', 'text', 'csv', 'powerpoint'])
const TYPE_LABEL = { local: 'Local', 'acc-dc': 'ACC · Desktop Connector', 'acc-web': 'ACC · Web via Chrome' }

export default function Projects({ projects, current, onPick, reload }) {
  const [sel, setSel] = useState(current || (projects[0] && projects[0].code))
  const [detail, setDetail] = useState(null)
  const [files, setFiles] = useState(null)
  const [kind, setKind] = useState('')
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [showNew, setShowNew] = useState(!projects.length)
  const [nw, setNw] = useState({ code: '', name: '', type: 'cad-to-bim', team: ['arc', 'str', 'mech', 'plumb', 'ff', 'elec', 'ict'] })
  const [types, setTypes] = useState([])
  useEffect(() => { api.projectTypes().then(setTypes).catch(() => {}) }, [])
  const typeOf = (id) => types.find((t) => t.id === id)
  const [src, setSrc] = useState({ name: '', type: 'acc-dc', path: '' })

  useEffect(() => { if (!sel && projects[0]) setSel(projects[0].code) }, [projects])
  useEffect(() => { if (sel) api.project(sel).then(setDetail).catch((e) => setErr(e.message)) }, [sel])
  useEffect(() => {
    if (!sel) return
    const t = setTimeout(() => api.files(sel, { kind, query: q }).then(setFiles), 250)
    return () => clearTimeout(t)
  }, [sel, kind, q])

  const run = async (label, fn) => { setBusy(label); setErr(''); try { await fn() } catch (e) { setErr(e.message) } finally { setBusy('') } }

  return (
    <div className="row">
      <aside className="rail">
        <div className="label">Projects</div>
        {projects.map((p) => (
          <button key={p.code} className="card" onClick={() => setSel(p.code)}
            style={{ textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 8, borderColor: sel === p.code ? '#F2A54188' : undefined }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span className="mono" style={{ color: 'var(--amber)', fontSize: 12 }}>{p.code}</span><span className="mute" style={{ fontSize: 11 }}>{p.stage}</span></div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>{p.name}</div>
            {p.type && <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span className="kind" style={{ color: '#F2C27B' }}>{p.type}</span>
              {p.progress && <span className="mute mono" style={{ fontSize: 11 }}>{p.progress[0]}/{p.progress[1]} stages</span>}</div>}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>{p.team.map((t) => <span key={t} className="kind" style={{ color: '#9CC7FF' }}>{t}</span>)}</div>
            <div className="mute" style={{ fontSize: 12, display: 'flex', gap: 12 }}><span>{p.agents} agents</span><span>{p.files ?? '—'} files</span><span style={{ color: p.open_issues ? 'var(--red)' : undefined }}>{p.open_issues} open issues</span></div>
          </button>
        ))}
        <button className="btn primary" onClick={() => setShowNew(!showNew)}>+ New project</button>
      </aside>

      <main className="page">
        {err && <div className="note err" role="alert">{err}</div>}
        {showNew && (
          <form className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12, borderColor: '#3A3220' }}
            onSubmit={(e) => { e.preventDefault(); run('create', async () => { await api.createProject(nw); await reload(); setSel(nw.code); setShowNew(false) }) }}>
            <b>New project</b>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <label style={{ flex: '0 1 140px' }}><span className="label">Code</span><input className="input mono" value={nw.code} required minLength={2} maxLength={6}
                onChange={(e) => setNw({ ...nw, code: e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '') })} /></label>
              <label style={{ flex: '1 1 260px' }}><span className="label">Name</span><input className="input" value={nw.name} onChange={(e) => setNw({ ...nw, name: e.target.value })} /></label>
            </div>
            <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
              <legend className="label" style={{ marginBottom: 6 }}>Project type — sets the workflow, QA gates, roles and skills</legend>
              <div className="typecards">
                {[...types, { id: '', title: 'Custom', title_ar: 'بدون workflow ثابت', summary: 'All five roles, no fixed stages.', stages: [] }].map((t) => (
                  <button type="button" key={t.id || 'custom'} aria-pressed={nw.type === t.id} className={'typecard' + (nw.type === t.id ? ' on' : '')}
                    onClick={() => setNw({ ...nw, type: t.id })}>
                    <b style={{ fontSize: 14 }}>{t.title}</b>
                    <span dir="rtl" className="mute" style={{ fontSize: 12 }}>{t.title_ar}</span>
                    <span className="dim" style={{ fontSize: 12 }}>{t.summary}</span>
                    {t.stages.length > 0 && <span className="mono" style={{ fontSize: 11, color: 'var(--amber)' }}>{t.stages.map((x) => x.id).join(' → ')}</span>}
                    {t.roles && <span className="mono dim" style={{ fontSize: 11 }}>roles: {t.roles.join(', ')}</span>}
                  </button>))}
              </div>
            </fieldset>
            <fieldset style={{ border: 0, padding: 0, margin: 0, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <legend className="label" style={{ marginBottom: 6 }}>Discipline teams (each = {(typeOf(nw.type)?.roles || ['leader', 'modeler', 'drafter', 'clash', 'info']).join(', ')})</legend>
              {DISCS.map((d) => { const on = nw.team.includes(d); return (
                <button type="button" key={d} aria-pressed={on} className={'chip' + (on ? ' on' : '')}
                  onClick={() => setNw({ ...nw, team: on ? nw.team.filter((x) => x !== d) : [...nw.team, d] })}>{d.toUpperCase()}</button>) })}
            </fieldset>
            <div><button className="btn primary" disabled={busy === 'create'}>{busy === 'create' ? 'Creating…' : 'Create project'}</button></div>
          </form>
        )}

        {detail && (<>
          <section style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: 16 }}>
            <div style={{ flex: '1 1 320px' }}>
              <div className="mono" style={{ color: 'var(--amber)' }}>{detail.code} · {detail.data.stage}</div>
              <h1 style={{ margin: '4px 0', fontSize: 26 }}>{detail.name}</h1>
              <div className="mute">{detail.type ? <span className="kind" style={{ color: '#F2C27B', marginRight: 8 }}>{detail.type}</span> : null}{detail.agents.length} agents · roles: {detail.roles.join(', ')}</div>
            </div>
            <button className="btn" onClick={() => run('scan', async () => { await api.scan(detail.code); setFiles(await api.files(detail.code, { kind, query: q })) })}>{busy === 'scan' ? 'Scanning…' : 'Scan files'}</button>
            <button className="btn primary" onClick={() => onPick(detail.code)}>Open in Studio 3D</button>
          </section>

          <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 16 }}>Sources <span className="mute" style={{ fontSize: 12, fontWeight: 400 }}>agents read only inside these · never modified</span></h2>
            <div className="card" style={{ padding: 0 }}>
              <table><thead><tr><th>Type</th><th>Name</th><th>Path / URL</th><th>Status</th></tr></thead><tbody>
                {detail.sources.map((s) => <tr key={s.name}><td>{TYPE_LABEL[s.type]}</td><td>{s.name}</td><td className="mono" style={{ fontSize: 12, wordBreak: 'break-all' }}>{s.path || s.url}</td>
                  <td style={{ color: s.readable ? 'var(--green)' : 'var(--mute)' }}>{s.readable ? 'readable' : s.type === 'acc-web' ? 'via Chrome' : 'path not found'}</td></tr>)}
              </tbody></table>
              <form style={{ display: 'flex', flexWrap: 'wrap', gap: 10, padding: 12, alignItems: 'flex-end' }}
                onSubmit={(e) => { e.preventDefault(); run('src', async () => { const d = await api.addSource(detail.code, src.type === 'acc-web' ? { name: src.name, type: src.type, url: src.path } : src); setDetail(d); setSrc({ ...src, name: '', path: '' }) }) }}>
                <label style={{ flex: '0 1 140px' }}><span className="label">Name</span><input className="input" required value={src.name} onChange={(e) => setSrc({ ...src, name: e.target.value })} placeholder="ACC" /></label>
                <label style={{ flex: '0 1 220px' }}><span className="label">Type</span>
                  <select className="input" value={src.type} onChange={(e) => setSrc({ ...src, type: e.target.value })}>
                    <option value="local">Local / network folder</option><option value="acc-dc">ACC · Desktop Connector</option><option value="acc-web">ACC · Web (Chrome)</option></select></label>
                <label style={{ flex: '1 1 320px' }}><span className="label">{src.type === 'acc-web' ? 'ACC project URL' : 'Folder path'}</span>
                  <input className="input mono" required value={src.path} onChange={(e) => setSrc({ ...src, path: e.target.value })}
                    placeholder={src.type === 'acc-dc' ? 'C:\\Users\\you\\DC\\ACCDocs\\Account\\Project\\Project Files' : src.type === 'acc-web' ? 'https://acc.autodesk.com/docs/files/projects/…' : 'D:\\Projects\\AOH'} /></label>
                <button className="btn teal" disabled={busy === 'src'}>Add source</button>
              </form>
            </div>
          </section>

          <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 16 }}>Files <span className="mute" style={{ fontSize: 12, fontWeight: 400 }}>{files ? `${files.matched} matched${files.scanned_at ? ' · scanned ' + files.scanned_at : ''}` : ''}</span></h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              {KINDS.map(([k, l]) => <button key={l} className={'chip' + (kind === k ? ' on' : '')} aria-pressed={kind === k} onClick={() => setKind(k)}>{l}</button>)}
              <div className="grow" />
              <label className="sr" htmlFor="fq">Search files</label>
              <input id="fq" className="input" style={{ maxWidth: 280 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search… (EIR, L03, MECH)" />
            </div>
            {files && files.error && <div className="note">{files.error}</div>}
            <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
              <table style={{ minWidth: 820 }}><thead><tr><th>File</th><th>Source</th><th>Kind</th><th>Disc.</th><th>ISO</th><th>Modified</th><th>Agents read</th></tr></thead><tbody>
                {(files?.files || []).map((f) => {
                  const parts = f.path.split('/'); const name = parts.pop()
                  return <tr key={f.source + f.path}><td><div className="mono" style={{ fontSize: 12, wordBreak: 'break-all' }}>{name}</div><div className="dim" style={{ fontSize: 11 }}>{parts.join('/')}</div></td>
                    <td className="mute">{f.source}</td><td><span className="kind">{f.kind}</span></td><td className="mono" style={{ color: '#9CC7FF' }}>{f.discipline || '—'}</td>
                    <td style={{ color: f.iso_name_ok ? 'var(--green)' : 'var(--amber)' }}>{f.iso_name_ok ? 'ok' : 'rename'}</td><td className="mono mute" style={{ fontSize: 12 }}>{f.modified}</td>
                    <td style={{ color: CONTENT.has(f.kind) ? 'var(--green)' : '#B6C0CC', fontSize: 12 }}>{CONTENT.has(f.kind) ? 'full content' : 'metadata · full via app'}</td></tr>
                })}
              </tbody></table>
            </div>
          </section>
        </>)}
      </main>
    </div>
  )
}
