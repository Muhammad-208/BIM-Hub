import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import * as THREE from 'three'
import { LAYER, ROLE_SHORT, agentColor } from '../api.js'

function label(text, color, size = 44) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128
  const x = c.getContext('2d')
  x.font = `600 ${size}px "IBM Plex Sans", system-ui, sans-serif`
  x.textAlign = 'center'; x.textBaseline = 'middle'
  const w = Math.min(500, x.measureText(text).width + 40)
  x.fillStyle = 'rgba(14,17,22,.78)'; x.beginPath()
  if (x.roundRect) x.roundRect(256 - w / 2, 24, w, 80, 18); else x.rect(256 - w / 2, 24, w, 80)
  x.fill(); x.fillStyle = color; x.fillText(text, 256, 66)
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }))
  s.scale.set(4, 1, 1); return s
}

/** Live org chart. Props: agents [{id, layer, discipline, role, title}], busy Set, selected, onSelect.
 *  ref.fire(from, to, color) sends a packet ("user" = the user's node above the manager). */
const Team3D = forwardRef(function Team3D({ agents, busy, selected, onSelect, autoRotate = true }, ref) {
  const canvasRef = useRef(null)
  const g = useRef(null)
  const live = useRef({ busy, selected })
  live.current = { busy, selected }

  useImperativeHandle(ref, () => ({
    fire(from, to, color = '#E6EAF0') {
      const s = g.current; if (!s) return
      const a = from === 'user' ? s.userPos : s.nodes[from]?.pos
      const b = to === 'user' ? s.userPos : s.nodes[to]?.pos
      if (!a || !b || a === b) return
      const mid = a.clone().add(b).multiplyScalar(0.5); mid.y += 1.6 + a.distanceTo(b) * 0.12
      const curve = new THREE.QuadraticBezierCurve3(a.clone(), mid, b.clone())
      const mesh = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 12), new THREE.MeshBasicMaterial({ color }))
      const trail = new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(40)), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.55 }))
      s.scene.add(mesh); s.scene.add(trail); s.packets.push({ mesh, trail, curve, t: 0 })
    },
    pulseHub() { if (g.current) g.current.hubPulse = performance.now() }
  }))

  useEffect(() => {
    const cv = canvasRef.current
    const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); renderer.setClearColor(0x0e1116, 0)
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 300)
    const scene = new THREE.Scene(); scene.fog = new THREE.Fog(0x0e1116, 36, 80)
    scene.add(new THREE.AmbientLight(0xffffff, 0.55))
    const dl = new THREE.DirectionalLight(0xffffff, 1.1); dl.position.set(8, 16, 10); scene.add(dl)
    const s = g.current = { scene, camera, renderer, nodes: {}, packets: [], orbit: { theta: 0.6, phi: 1.1, r: 32, tr: 32 }, target: new THREE.Vector3(0, 2.4, 0), t0: performance.now() }

    const byId = Object.fromEntries(agents.map((a) => [a.id, a]))
    const discs = [...new Set(agents.filter((a) => a.discipline).map((a) => a.discipline))]
    const qa = agents.filter((a) => a.layer === 2)
    const tiers = { 4: 9.2, 3: 6.0, 2: 2.8, 1: -0.8 }
    const R1 = Math.max(7.5, discs.length * 1.35)
    ;[[4, 1.6], [3, 1.6], [2, 5.2], [1, R1 + 2.2]].forEach(([L, R]) => {
      const col = new THREE.Color(LAYER[L].color)
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(R, R, 0.06, 72), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.06 }))
      disc.position.y = tiers[L] - 1.4; scene.add(disc)
      const ring = new THREE.Mesh(new THREE.TorusGeometry(R, 0.015, 8, 128), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.35 }))
      ring.rotation.x = Math.PI / 2; ring.position.y = tiers[L] - 1.37; scene.add(ring)
    })
    const node = (a, pos, radius, text, scale) => {
      if (!a) return
      const color = agentColor(a), col = new THREE.Color(color)
      const grp = new THREE.Group(); grp.position.copy(pos)
      const core = new THREE.Mesh(new THREE.IcosahedronGeometry(radius, 2), new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 0.35, roughness: 0.35, metalness: 0.2, flatShading: true }))
      core.userData.agent = a.id; grp.add(core)
      const halo = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.6, 0.035, 8, 48), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.22 }))
      halo.rotation.x = Math.PI / 2; grp.add(halo)
      const sel = new THREE.Mesh(new THREE.TorusGeometry(radius * 2, 0.045, 8, 48), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 }))
      sel.rotation.x = Math.PI / 2; grp.add(sel)
      const lab = label(text, color); lab.position.set(0, radius + 0.75, 0); lab.scale.multiplyScalar(scale); grp.add(lab)
      scene.add(grp); s.nodes[a.id] = { core, halo, sel, pos: pos.clone() }
    }
    const line = (pa, pb, c, o) => pa && pb && scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([pa, pb]), new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: o })))
    node(byId['bim-manager'], new THREE.Vector3(0, tiers[4], 0), 0.8, 'BIM Manager', 1)
    node(byId['bim-coordinator'], new THREE.Vector3(0, tiers[3], 0), 0.75, 'BIM Coordinator', 1)
    qa.forEach((a, i) => { const an = (i / qa.length) * Math.PI * 2 + 0.5; node(a, new THREE.Vector3(Math.sin(an) * 3.6, tiers[2], Math.cos(an) * 3.6), 0.58, a.title, 0.9) })
    line(s.nodes['bim-manager']?.pos, s.nodes['bim-coordinator']?.pos, 0xF2A541, 0.5)
    qa.forEach((a) => line(s.nodes['bim-coordinator']?.pos, s.nodes[a.id]?.pos, 0xA78BFA, 0.4))
    discs.forEach((d, i) => {
      const an = (i / discs.length) * Math.PI * 2 + 0.2
      const lp = new THREE.Vector3(Math.sin(an) * R1, tiers[1], Math.cos(an) * R1)
      node(byId[d + '-leader'], lp, 0.55, d.toUpperCase(), 0.95)
      line(s.nodes['bim-coordinator']?.pos, lp, 0xA78BFA, 0.2)
      qa.forEach((q) => line(s.nodes[q.id]?.pos, lp, 0x2DD4BF, 0.08))
      const roles = agents.filter((a) => a.discipline === d && a.role !== 'leader')
      roles.forEach((a, j) => {
        const sa = an + (j - (roles.length - 1) / 2) * 0.24 * (9 / Math.max(discs.length, 6)), rr = R1 + 1.7 + (j % 2) * 0.5
        const sp = new THREE.Vector3(Math.sin(sa) * rr, tiers[1] - 1.0 - (j % 2) * 0.25, Math.cos(sa) * rr)
        node(a, sp, 0.26, ROLE_SHORT[a.role] || a.role, 0.55); line(lp, sp, 0x60A5FA, 0.35)
      })
    })
    const hub = new THREE.Mesh(new THREE.TorusKnotGeometry(1.0, 0.24, 160, 12), new THREE.MeshStandardMaterial({ color: 0x2DD4BF, emissive: 0x2DD4BF, emissiveIntensity: 0.25, roughness: 0.4, transparent: true, opacity: 0.85 }))
    hub.position.set(0, -4.4, 0); scene.add(hub); s.hub = hub
    const hl = label('Learning Hub', '#2DD4BF', 40); hl.position.set(0, -6, 0); scene.add(hl)
    s.userPos = new THREE.Vector3(0, 13.2, 0)
    const ul = label('You', '#E6EAF0', 40); ul.position.copy(s.userPos); scene.add(ul)

    const resize = () => { const w = cv.clientWidth || 800, h = cv.clientHeight || 500; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix() }
    resize(); const ro = new ResizeObserver(resize); ro.observe(cv)
    let down = null
    const pd = (e) => { down = { x: e.clientX, y: e.clientY, th: s.orbit.theta, ph: s.orbit.phi, moved: false }; cv.setPointerCapture(e.pointerId) }
    const pm = (e) => { if (!down) return; const dx = e.clientX - down.x, dy = e.clientY - down.y; if (Math.abs(dx) + Math.abs(dy) > 4) down.moved = true
      s.orbit.theta = down.th - dx * 0.006; s.orbit.phi = Math.max(0.35, Math.min(1.45, down.ph - dy * 0.005)); s.touched = performance.now() }
    const pu = (e) => {
      if (down && !down.moved) {
        const r = cv.getBoundingClientRect(), ray = new THREE.Raycaster()
        ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera)
        const hit = ray.intersectObjects(Object.values(s.nodes).map((n) => n.core))[0]
        if (hit) onSelect(hit.object.userData.agent)
      }
      down = null
    }
    const wh = (e) => { e.preventDefault(); s.orbit.tr = Math.max(10, Math.min(70, s.orbit.tr + e.deltaY * 0.02)) }
    cv.addEventListener('pointerdown', pd); cv.addEventListener('pointermove', pm); cv.addEventListener('pointerup', pu); cv.addEventListener('wheel', wh, { passive: false })

    let raf
    const frame = () => {
      const now = performance.now(), t = (now - s.t0) / 1000, { busy: b, selected: sl } = live.current
      if (autoRotate && (!s.touched || now - s.touched > 4000)) s.orbit.theta += 0.0016
      s.orbit.r += (s.orbit.tr - s.orbit.r) * 0.08
      const o = s.orbit
      camera.position.set(o.r * Math.sin(o.phi) * Math.sin(o.theta), s.target.y + o.r * Math.cos(o.phi), o.r * Math.sin(o.phi) * Math.cos(o.theta)); camera.lookAt(s.target)
      for (const [id, n] of Object.entries(s.nodes)) {
        const w = b.has(id)
        n.core.rotation.y = t * (w ? 1.6 : 0.25)
        n.core.material.emissiveIntensity = w ? 0.75 + Math.sin(t * 6) * 0.25 : 0.3
        const k = w ? 1 + Math.sin(t * 5) * 0.12 : 1; n.halo.scale.set(k, k, k); n.halo.material.opacity = w ? 0.7 : 0.22
        n.sel.material.opacity = sl === id ? 0.85 : 0; n.sel.rotation.z = t
      }
      hub.rotation.y = t * 0.4; hub.material.emissiveIntensity = s.hubPulse && now - s.hubPulse < 2500 ? 0.9 : 0.25
      for (let i = s.packets.length - 1; i >= 0; i--) {
        const p = s.packets[i]; p.t += 0.012
        if (p.t >= 1) { scene.remove(p.mesh); scene.remove(p.trail); p.mesh.geometry.dispose(); p.trail.geometry.dispose(); s.packets.splice(i, 1); continue }
        p.mesh.position.copy(p.curve.getPoint(p.t)); p.trail.material.opacity = 0.55 * (1 - p.t)
      }
      renderer.render(scene, camera); raf = requestAnimationFrame(frame)
    }
    frame()
    return () => { cancelAnimationFrame(raf); ro.disconnect(); cv.removeEventListener('pointerdown', pd); cv.removeEventListener('pointermove', pm); cv.removeEventListener('pointerup', pu); cv.removeEventListener('wheel', wh); renderer.dispose(); g.current = null }
  }, [agents.map((a) => a.id).join(',')])

  return <canvas ref={canvasRef} role="img" aria-label="3D view of the agent team; click a node to talk to it" />
})
export default Team3D
