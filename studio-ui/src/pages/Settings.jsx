import React, { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function Settings({ auth, onChange }) {
  const [s, setS] = useState(null)
  const [key, setKey] = useState('')
  const [msg, setMsg] = useState('')
  useEffect(() => { api.settings().then(setS) }, [])
  if (!s) return <div className="page">Loading…</div>
  const save = async (patch) => { const n = await api.saveSettings(patch); setS(n); setMsg('Saved'); onChange() }
  return (
    <div className="page" style={{ maxWidth: 860 }}>
      <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16 }}>Claude connection</h2>
        <div className="mono mute" style={{ fontSize: 12 }}>
          {auth ? (auth.installed ? `Claude Code ${auth.version || ''} · ${auth.path} · login: ${auth.authMethod || 'unknown'}` : auth.error) : 'checking…'}
        </div>
        <fieldset style={{ border: 0, padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <legend className="label" style={{ marginBottom: 8 }}>Mode</legend>
          <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <input type="radio" name="mode" checked={s.auth_mode === 'subscription'} onChange={() => save({ auth_mode: 'subscription' })} />
            <span><b>Claude subscription</b> — uses your own Claude Code login (<span className="mono">claude auth login</span>). No API key, no extra cost. For your personal use on this PC.</span>
          </label>
          <label style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <input type="radio" name="mode" checked={s.auth_mode === 'api_key'} onChange={() => save({ auth_mode: 'api_key' })} />
            <span><b>API key</b> — pay per use. Required when the app is used by others or as a product, and for unattended runs.</span>
          </label>
        </fieldset>
        {s.auth_mode === 'api_key' && (
          <form onSubmit={async (e) => { e.preventDefault(); await api.setKey(key); setKey(''); setS(await api.settings()); onChange(); setMsg('Key saved') }}
            style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <label style={{ flex: '1 1 320px' }}><span className="label">Anthropic API key {s.api_key_set ? '(set)' : '(not set)'}</span>
              <input className="input mono" type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder="sk-ant-…" autoComplete="off" />
            </label>
            <label style={{ flex: '0 1 180px' }}><span className="label">Budget cap per run (USD, 0 = none)</span>
              <input className="input" type="number" min="0" step="0.5" value={s.max_budget_usd} onChange={(e) => setS({ ...s, max_budget_usd: +e.target.value })} onBlur={() => save({ max_budget_usd: s.max_budget_usd })} />
            </label>
            <button className="btn primary" type="submit">Save key</button>
          </form>
        )}
      </section>
      <section className="card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(240px,1fr))', gap: 12 }}>
        <label style={{ gridColumn: '1/-1' }}><span className="label">BIM Hub folder (restart the app after changing)</span>
          <input className="input mono" value={s.hub_root} onChange={(e) => setS({ ...s, hub_root: e.target.value })} onBlur={() => save({ hub_root: s.hub_root })} placeholder="E:\Ai\BIM Hub" /></label>
        <label><span className="label">Claude Code path (empty = auto)</span>
          <input className="input mono" value={s.claude_path} onChange={(e) => setS({ ...s, claude_path: e.target.value })} onBlur={() => save({ claude_path: s.claude_path })} placeholder="C:\Users\you\.local\bin\claude.exe" /></label>
        <label><span className="label">Model (empty = default)</span>
          <input className="input mono" value={s.model} onChange={(e) => setS({ ...s, model: e.target.value })} onBlur={() => save({ model: s.model })} placeholder="opus / sonnet" /></label>
        <label><span className="label">Permission mode</span>
          <select className="input" value={s.permission_mode} onChange={(e) => save({ permission_mode: e.target.value })}>
            <option value="dontAsk">dontAsk — only allowed tools run (recommended)</option>
            <option value="acceptEdits">acceptEdits — also file edits</option>
            <option value="plan">plan — read-only planning</option>
          </select></label>
        <label><span className="label">Reply language</span>
          <select className="input" value={s.language} onChange={(e) => save({ language: e.target.value })}>
            <option value="ar-EG">Egyptian Arabic</option><option value="en">English</option>
          </select></label>
        <label style={{ gridColumn: '1/-1' }}><span className="label">Tools agents may use without asking (space-separated)</span>
          <input className="input mono" value={s.allowed_tools.join(' ')} onChange={(e) => setS({ ...s, allowed_tools: e.target.value.split(/\s+/).filter(Boolean) })} onBlur={() => save({ allowed_tools: s.allowed_tools })} /></label>
      </section>
      {msg && <div className="mute" role="status">{msg}</div>}
    </div>
  )
}
