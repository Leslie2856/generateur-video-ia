import { useRef, useState } from 'react'
import { Clapperboard, ImagePlus, Sparkles, Upload, WandSparkles, Clock3, MonitorPlay, AlertCircle } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [mode, setMode] = useState('text')
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(10)
  const [ratio, setRatio] = useState('16:9')
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const fileRef = useRef(null)

  async function generate(e) {
    e.preventDefault()
    setNotice('')
    if (prompt.trim().length < 3) {
      setNotice('Décris ta vidéo avec au moins quelques mots.')
      return
    }
    if (mode === 'image' && !file) {
      setNotice('Ajoute une image pour utiliser le mode Image vers vidéo.')
      return
    }
    setBusy(true)
    try {
      let response
      if (mode === 'text') {
        response = await fetch(API + '/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, duration_seconds: Number(duration), aspect_ratio: ratio }),
        })
      } else {
        const data = new FormData()
        data.append('prompt', prompt)
        data.append('duration_seconds', String(duration))
        data.append('aspect_ratio', ratio)
        data.append('image', file)
        response = await fetch(API + '/api/jobs/image-to-video', { method: 'POST', body: data })
      }
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data.detail || 'Impossible de démarrer la génération.')
      setNotice('Demande envoyée.')
    } catch (err) {
      setNotice(err.message + ' L’interface est prête, mais un moteur vidéo réel doit encore être connecté.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-icon"><Clapperboard size={21} /></span><span>motion<span className="brand-accent">lab</span><small>STUDIO IA</small></span></a><div className="top-actions"><span className="status-dot" /><span className="beta">BÊTA</span><a className="github-link" href="https://github.com/Leslie2856/generateur-video-ia" target="_blank" rel="noreferrer">GitHub ↗</a></div></header>
    <main id="top" className="main-grid">
      <section className="intro"><div className="eyebrow"><Sparkles size={14} /> TON IMAGINATION, EN MOUVEMENT</div><h1>Transforme tes idées<br />en <span>vidéos.</span></h1><p className="intro-copy">Décris une scène ou apporte une image. Prépare ta création vidéo avec l’IA, selon ton format et ta durée.</p><div className="feature-row"><div><WandSparkles size={17}/><span>Texte en vidéo</span></div><div><ImagePlus size={17}/><span>Image en vidéo</span></div><div><Clock3 size={17}/><span>Jusqu’à 3 min</span></div></div><div className="preview-card"><div className="preview-orbit orbit-one"/><div className="preview-orbit orbit-two"/><div className="preview-center"><Clapperboard size={38}/><span>TON PROCHAIN FILM</span><small>COMMENCE ICI</small></div><div className="preview-chip chip-top">✦ Créativité sans limite</div><div className="preview-chip chip-bottom">FORMAT · {ratio}</div></div></section>
      <section className="studio-card"><div className="studio-heading"><div><div className="section-kicker">ESPACE DE CRÉATION</div><h2>Nouvelle vidéo</h2></div><span className="step-tag">01 <span>/ 03</span></span></div>
        <div className="mode-tabs"><button className={mode === 'text' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('text'); setNotice('') }} type="button"><WandSparkles size={17}/> Texte vers vidéo</button><button className={mode === 'image' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('image'); setNotice('') }} type="button"><ImagePlus size={17}/> Image vers vidéo</button></div>
        <form onSubmit={generate}><label className="field-label" htmlFor="prompt">DÉCRIS TA VIDÉO <span>REQUIS</span></label><textarea id="prompt" value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={4000} placeholder={mode === 'text' ? 'Ex. : Un coucher de soleil doré sur les dunes du Sahel, caméra qui avance lentement, style cinématographique…' : 'Ex. : Fais doucement avancer la caméra, ajoute un léger mouvement au vent et une lumière cinématographique…'} rows={5}/><div className="field-footer"><span>Un prompt précis donne une meilleure direction créative.</span><span>{prompt.length}/4000</span></div>
        {mode === 'image' && <div className="upload-zone" onClick={() => fileRef.current?.click()} role="button" tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileRef.current?.click() }}><input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e => setFile(e.target.files?.[0] || null)}/><Upload size={22}/><strong>{file ? file.name : 'Choisir une image de départ'}</strong><span>PNG, JPG ou WebP</span></div>}
        <div className="settings-grid"><div><label className="field-label" htmlFor="duration">DURÉE</label><div className="select-wrap"><Clock3 size={16}/><select id="duration" value={duration} onChange={e => setDuration(e.target.value)}>{[5,10,15,30,60,90,120,180].map(n => <option value={n} key={n}>{n >= 60 ? (n / 60) + ' min' : n + ' secondes'}</option>)}</select></div></div><div><label className="field-label" htmlFor="ratio">FORMAT</label><div className="select-wrap"><MonitorPlay size={16}/><select id="ratio" value={ratio} onChange={e => setRatio(e.target.value)}><option value="16:9">16:9 · Paysage</option><option value="9:16">9:16 · Portrait</option><option value="1:1">1:1 · Carré</option></select></div></div></div>
        <div className="provider-note"><AlertCircle size={17}/><span><strong>Moteur vidéo à connecter</strong> — ce prototype prépare l’interface et l’API. La génération réelle sera activée après le choix d’un modèle ou fournisseur vidéo.</span></div>
        {notice && <div className="notice" role="status">{notice}</div>}
        <button className="generate-button" type="submit" disabled={busy}>{busy ? 'Connexion à l’API…' : <><Sparkles size={18}/> Préparer ma génération <span>↗</span></>}</button><p className="fine-print">Aucune vidéo n’est simulée ni présentée comme générée.</p></form>
      </section>
    </main><footer><span>motionlab · STUDIO IA</span><span>Un projet en construction, étape par étape.</span></footer>
  </div>
}
