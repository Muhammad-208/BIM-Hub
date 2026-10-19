import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, LAYER, ROLE_SHORT, agentColor, hhmm } from '../api.js'
import Team3D from '../components/Team3D.jsx'

const ROLE_ORDER = ['leader', 'modeler', 'drafter', 'clash', 'info']

export default function Studio({ code }) {
  const [detail, setDetail] = useState(null)
  const [state, setState] = useState(null)
  const [sel, setSel] = useState('bim-manager')
  const [live, setLive] = useState([])            // events of the current session (runs + activity)
  const [recent, setRecent] = useState({})        // agent → last activity ms
  const [tab, setTab] = useState('activity')
  const [draft, setDraft] = useState('')
  const [issue, setIssue] = useState(null)
  const [err, setErr] = useState('')
  const three = useRef(null)
  const refreshT = useRef(null)

  const refresh = useCallback(() => api.state(code).then(setState).catch((e) => setErr(e.message)), [code])
  const soon = () => { clearTimeout(refreshT.current); refreshT.current = setTimeout(refresh, 600) }

  useEffect(() => { api.project(code).then(setDetail).catch((e) => setErr(e.message)); refresh() }, [code])

  useEffect(() => {
    const es = api.events(code)
    es.onmessage = (m) => {
      let ev; try { ev = JSON.parse(m.data) } catch { return }
      const who = (ev.agent || '').replace('›sub', '')
      if (who) setRecent((r) => ({ ...r, [who]: Date.now() }))
      const f = three.current
      if (f) {
        if (ev.kind === 'user') f.fire('user', ev.agent, '#E6EAF0')
        if (ev.kind === 'tool' && ev.target) f.fire(who, ev.target, agentColor({ layer: 2 }))
        if (ev.kind === 'activity') {
          const a = ev.args || {}
          if (ev.tool === 'message_send' && a.to) f.fire(ev.agent, a.to, '#A78BFA')
          if (ev.tool === 'issue_create' && a.owner) f.fire(ev.agent, a.owner, '#F87171')
          if (ev.tool === 'lesson_propose') f.fire(ev.agent, 'bim-manager', '#2DD4BF')
          if (ev.tool === 'lesson_approve') f.pulseHub()
        }
        if (ev.kind === 'done' && !ev.is_error) f.fire(who, 'user', '#F2A541')
        if (ev.kind === 'lesson') f.pulseHub()
      }
      setLive((l) => [...l.slice(-400), ev])
      if (['end', 'activity', 'scan', 'lesson'].includes(ev.kind)) soon()
    }
    return () => es.close()
  }, [code])

  const agents = detail?.agents || []
  const byId = useMemo(() => Object.fromEntries(agents.map((a) => [a.id, a])), [agents])
  const runningAgents = new Set((state?.running || []).map((r) => r.agent))
  live.forEach((e) => { if (e.kind === 'start') runningAgents.add(e.agent); if (e.kind === 'end') runningAgents.delete(e.agent) })
  const busy = new Set([...runningAgents, ...Object.entries(recent).filter(([, t]) => Date.now() - t < 8000).map(([a]) => a)])
  const [, tick] = useState(0)
  useEffect(() => { const t = setInterval(() => tick((x) => x + 1), 2000); return () => clearInterval(t) }, [])

  const send = async (e) => {
    e.preventDefault()
    const text = draft.trim(); if (!text) return
    setDraft(''); setErr('')
    try { await api.chat(code, sel, text, issue ? { issue: issue.id } : undefined) } catch (x) { setErr(x.message) }
  }

  if (!detail) return <div className="page">{err || 'Loading…'}</div>
  const a = byId[sel] || agents[0]
  const discs = [...new Set(agents.filter((x) => x.discipline).map((x) => x.discipline))]

  // chat for the selected agent: stored transcript + live run events
  const chat = (state?.chat || []).filter((c) => c.from === sel || c.to === sel)
  const runIds = new Set(chat.map((c) => c.run))
  const liveForSel = live.filter((e) => (e.agent || '').replace('›sub', '') === sel && ['text', 'tool', 'error'].includes(e.kind) && !e.persisted)
  const activity = [...(state?.activity || []).map((x) => ({ ...x, kind: 'activity' })), ...live.filter((e) => e.kind === 'activity' || e.kind === 'tool')]
    .slice(-300).reverse()

  return (
    <div className="row">
      <aside className="rail" aria-label="Team">
        <div className="label">Team · {code}</div>
        {[4, 3, 2].map((L) => (
          <div key={L}>
            <div className="pill mute" style={{ fontSize: 11, padding: '4px 6px' }}><span className="dot" style={{ background: LAYER[L].color, borderRadius: 3 }} />{LAYER[L].label}</div>
            {agents.filter((x) => x.layer === L).map((x) => (
              <button key={x.id} className={'agentRow' + (sel === x.id ? ' on' : '')} onClick={() => setSel(x.id)}>
                <span className="dot" style={{ background: busy.has(x.id) ? 'var(--amber)' : LAYER[L].color }} />
                <span className="grow">{x.title}</span>
                <span className="mono" style={{ fontSize: 11, color: busy.has(x.id) ? 'var(--amber)' : 'var(--dim)' }}>{busy.has(x.id) ? 'working' : 'idle'}</span>
              </button>))}
          </div>))}
        <div>
          <div className="pill mute" style={{ fontSize: 11, padding: '4px 6px' }}><span className="dot" style={{ background: LAYER[1].color, borderRadius: 3 }} />{LAYER[1].label}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {discs.map((d) => (
              <div key={d} className="disc">
                <b style={{ fontSize: 13 }}>{d.toUpperCase()}</b>
                <div className="roles">
                  {ROLE_ORDER.filter((r) => byId[`${d}-${r}`]).map((r) => {
                    const id = `${d}-${r}`
                    return <button key={id} title={byId[id].title} aria-label={'Chat with ' + byId[id].title} onClick={() => setSel(id)}
                      className={[r === 'leader' && 'leader', sel === id && 'on', busy.has(id) && 'busy'].filter(Boolean).join(' ')}>{ROLE_SHORT[r]}</button>
                  })}
                </div>
              </div>))}
          </div>
        </div>
      </aside>

      <main className="center">
        <div className="stage">
          <Team3D ref={three} agents={agents} busy={busy} selected={sel} onSelect={setSel} />
          <div className="overlay">{[4, 3, 2, 1].map((L) => <span key={L} className="pill"><span className="dot" style={{ background: LAYER[L].color }} />{LAYER[L].label}</span>)}</div>
          <div className="dim" style={{ position: 'absolute', left: 14, bottom: 10, fontSize: 11, pointerEvents: 'none' }}>drag to orbit · scroll to zoom · click a node to talk to it · packets = real hand-offs and tool calls</div>
        </div>
        <div className="tabs" role="tablist">
          {[...(state?.workflow?.length ? [['workflow', 'Workflow']] : []), ['activity', 'Activity'], ['issues', `Issues ${state ? state.issues.filter((i) => !['resolved', 'closed'].includes(i.status)).length : ''}`], ['messages', 'Messages'],
            ['cde', 'CDE'], ['zones', 'Zones'], ['health', 'Health'], ['dash', 'Dashboards'], ['hub', `Learning Hub ${state?.lessons?.filter((l) => l.status === 'pending').length || ''}`]]
            .map(([k, l]) => <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>)}
        </div>
        <div className="panel">
          {tab === 'workflow' && <Workflow stages={state?.workflow || []} type={detail.type} onPick={setSel} />}
          {tab === 'activity' && (activity.length ? activity.map((e, i) => (
            <div className="line" key={i}><span className="dim" style={{ width: 64 }}>{hhmm(e.at)}</span>
              <span style={{ width: 130, color: agentColor(byId[(e.agent || '').replace('›sub', '')]) }}>{e.agent || '—'}</span>
              <span className="mute" style={{ width: 90 }}>{e.server || 'claude'}</span>
              <span style={{ flex: 1, color: e.ok === false ? 'var(--red)' : undefined }}>{e.tool}{e.target ? ' → ' + e.target : ''} {e.args ? JSON.stringify(e.args) : e.input || ''}{e.error ? ' · ' + e.error : ''}</span></div>))
            : <div className="dim">No activity yet. Talk to an agent here or in Claude Code — every MCP call shows up live.</div>)}
          {tab === 'issues' && <table><thead><tr><th>ID</th><th>Title</th><th>Owner</th><th>Priority</th><th>Status</th></tr></thead><tbody>
            {(state?.issues || []).slice().reverse().map((i) => <tr key={i.id} onClick={() => setIssue(i)} style={{ cursor: 'pointer', background: issue?.id === i.id ? '#1C232C' : undefined }}>
              <td className="mono" style={{ color: 'var(--red)' }}>{i.id}</td><td>{i.title}<div className="dim" style={{ fontSize: 11 }}>{i.location}</div></td><td className="mono">{i.owner}</td><td>{i.priority}</td>
              <td style={{ color: ['resolved', 'closed'].includes(i.status) ? 'var(--green)' : 'var(--red)' }}>{i.status}</td></tr>)}</tbody></table>}
          {tab === 'messages' && (state?.messages || []).filter((m) => m.from).slice().reverse().map((m) => (
            <div className="line" key={m.id}><span className="dim" style={{ width: 64 }}>{hhmm(m.at)}</span><span style={{ width: 230 }}>{m.from} → {m.to}</span><span style={{ flex: 1, fontFamily: 'IBM Plex Sans' }} dir="auto">{m.task}</span></div>))}
          {tab === 'cde' && <table><thead><tr><th>Container</th><th>State</th><th>QA model</th><th>QA data</th><th>QA doc</th><th>Updated</th></tr></thead><tbody>
            {Object.entries(state?.models || {}).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td>{v.state}</td><td>{v.qa_model || '—'}</td><td>{v.qa_data || '—'}</td><td>{v.qa_doc || '—'}</td><td className="dim">{(v.updated_at || '').slice(0, 16)} · {v.updated_by}</td></tr>)}</tbody></table>}
          {tab === 'zones' && <table><thead><tr><th>Zone</th><th>Status</th><th>By</th><th>Note</th></tr></thead><tbody>
            {Object.entries(state?.zones || {}).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td style={{ color: v.status === 'coordinated' ? 'var(--green)' : 'var(--amber)' }}>{v.status}</td><td>{v.by}</td><td>{v.note}</td></tr>)}</tbody></table>}
          {tab === 'health' && <table><thead><tr><th>Model</th><th>Discipline</th><th>Score</th><th>Failed checks</th><th>By</th><th>At</th></tr></thead><tbody>
            {(state?.health || []).map((h) => <tr key={h.model}><td className="mono">{h.model}</td><td>{h.discipline}</td><td style={{ color: h.score >= 90 ? 'var(--green)' : h.score >= 75 ? 'var(--amber)' : 'var(--red)' }}>{h.score}</td><td>{h.failed}</td><td>{h.by}</td><td className="dim">{(h.at || '').slice(0, 16)}</td></tr>)}</tbody></table>}
          {tab === 'dash' && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(230px,1fr))', gap: 10 }}>
            {Object.values(state?.dashboards || {}).map((d) => <a key={d.kind} className="card" href={api.dashboardUrl(code, d.kind)} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <b>{d.title || d.kind}</b><div style={{ display: 'flex', gap: 16 }}>{(d.kpis || []).slice(0, 3).map((k) => <div key={k.label}><div style={{ fontSize: 22, fontWeight: 700 }}>{k.value}</div><div className="mute" style={{ fontSize: 11 }}>{k.label}</div></div>)}</div>
              <span className="dim" style={{ fontSize: 11 }}>{d.by} · {(d.at || '').slice(0, 16)} · open ↗</span></a>)}
            {!Object.keys(state?.dashboards || {}).length && <div className="dim">No dashboards yet — ask the BIM Coordinator to publish them.</div>}</div>}
          {tab === 'hub' && (state?.lessons || []).map((l) => <div key={l.id} className="line" style={{ fontFamily: 'IBM Plex Sans', alignItems: 'center' }}>
            <span className="mono" style={{ width: 110, color: 'var(--teal)' }}>{l.proposed_by}</span><span style={{ flex: 1 }}>{l.title}</span>
            <span className="mono" style={{ color: l.status === 'pending' ? 'var(--amber)' : 'var(--green)' }}>{l.status}</span>
            {l.status === 'pending' && <button className="btn teal" style={{ minHeight: 32 }} onClick={async () => { await api.approveLesson(code, l.id); three.current?.pulseHub(); refresh() }}>Approve</button>}</div>)}
        </div>
      </main>

      <section className="side" aria-label="Chat">
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="mono" style={{ width: 36, height: 36, borderRadius: '50%', background: agentColor(a), color: '#0E1116', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 11 }}>
            {a?.role ? ROLE_SHORT[a.role] : (a?.id || '').split('-').map((x) => x[0]).join('').toUpperCase()}</span>
          <div style={{ minWidth: 0, flex: 1 }}><div style={{ fontWeight: 600 }}>{a?.title}</div>
            <div className="mute" style={{ fontSize: 12 }}>L{a?.layer} · <span style={{ color: busy.has(sel) ? 'var(--amber)' : undefined }}>{busy.has(sel) ? 'working' : 'idle'}</span></div></div>
          <button className="btn" style={{ minHeight: 30, fontSize: 12 }} title="Start a fresh conversation with this agent" onClick={() => api.resetAgent(code, sel)}>New chat</button>
        </div>
        <div className="chatlog">
          {!chat.length && !liveForSel.length && <div className="dim" dir="auto" style={{ fontSize: 13 }}>اكتب لـ {a?.title}. الرسالة بتتحوّل لـ Claude Code بالصيغة المناسبة وبتشتغل جوه مشروع {code}.</div>}
          {chat.map((c, i) => c.from === 'user'
            ? <div key={i} className="bubble me" dir="auto">{c.text}</div>
            : <div key={i} className="bubble them" dir="auto" style={c.error ? { borderColor: '#F8717188', color: 'var(--red)' } : undefined}>{c.error || c.text}
                {c.cost_usd != null && <div className="dim mono" style={{ fontSize: 10, marginTop: 6 }}>{c.turns} turns · ${Number(c.cost_usd).toFixed(3)}</div>}</div>)}
          {liveForSel.filter((e) => !runIds.has(e.run) || e.kind !== 'text').slice(-30).map((e, i) => e.kind === 'tool'
            ? <div key={'l' + i} className="toolline">⚙ {e.tool.replace(/^mcp__/, '').replace('__', ' · ')}{e.target ? ' → ' + e.target : ''}</div>
            : e.kind === 'error' ? <div key={'l' + i} className="bubble them err">{e.error}</div>
            : runIds.has(e.run) ? null : <div key={'l' + i} className="bubble them" dir="auto" style={{ opacity: 0.8 }}>{e.text}</div>)}
        </div>
        {issue && <div className="note" style={{ margin: '0 12px' }}>Context: <span className="mono">{issue.id}</span> {issue.title} <button className="btn" style={{ minHeight: 26, fontSize: 11, marginLeft: 6 }} onClick={() => setIssue(null)}>×</button></div>}
        {err && <div className="note err" style={{ margin: '6px 12px' }}>{err}</div>}
        <form onSubmit={send} style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--line)' }}>
          <label className="sr" htmlFor="msg">Message</label>
          <textarea id="msg" className="input" rows={2} dir="auto" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={`اكتب لـ ${a?.title}…`}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e) } }} style={{ resize: 'vertical' }} />
          <button className="btn primary" type="submit" disabled={runningAgents.has(sel)}>{runningAgents.has(sel) ? '…' : 'Send'}</button>
        </form>
      </section>
    </div>
  )
}

const ST_COLOR = { done: 'var(--green)', 'qa-pass': 'var(--teal)', 'qa-fail': 'var(--red)', blocked: 'var(--red)',
  review: '#A78BFA', 'in-progress': 'var(--amber)', todo: 'var(--dim)' }

function Workflow({ stages, type, onPick }) {
  const done = stages.reduce((n, s) => n + s.done, 0), total = stages.reduce((n, s) => n + s.total, 0)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div className="mute" style={{ fontSize: 12 }}><span className="mono" style={{ color: 'var(--amber)' }}>{type}</span> · {done}/{total} stage items done
        · flow: todo → in-progress → review → qa-pass → done (coordinator / manager)</div>
      <div className="wfbar" aria-hidden="true">{stages.map((s) => <span key={s.id} title={s.id + ' ' + s.title}
        style={{ flex: 1, background: ST_COLOR[s.status], opacity: s.status === 'todo' ? .35 : 1 }} />)}</div>
      {stages.map((s) => (
        <div key={s.id} className="card" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8, opacity: s.optional && s.status === 'todo' ? .7 : 1 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }}>
            <b className="mono" style={{ color: 'var(--amber)' }}>{s.id}</b><b>{s.title}</b>{s.optional && <span className="kind">optional</span>}
            <span className="grow" /><span className="mono" style={{ fontSize: 12, color: ST_COLOR[s.status] }}>{s.status} · {s.done}/{s.total}</span>
          </div>
          <div className="mute" style={{ fontSize: 12 }}>{s.done_when}{s.gate.length ? ' · QA gate: ' + s.gate.join(', ') : ''}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {s.items.map((i) => (
              <button key={i.key} className="chip" onClick={() => i.owner[0] && onPick(i.owner[0])}
                title={(i.note || '') + (i.by ? ' · ' + i.by + ' ' + (i.at || '').slice(0, 16) : '')}
                style={{ borderColor: ST_COLOR[i.status], color: i.status === 'todo' ? undefined : ST_COLOR[i.status] }}>
                {i.discipline ? i.discipline.toUpperCase() : (i.owner[0] || s.owner)} · {i.status}</button>))}
          </div>
        </div>))}
    </div>)
}
