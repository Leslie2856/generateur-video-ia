import { useEffect, useRef, useState } from 'react'
import { Clapperboard, ImagePlus, Sparkles, Upload, WandSparkles, Clock3, MonitorPlay, AlertCircle, Download } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [mode, setMode] = useState('text')
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(5)
  const [ratio, setRatio] = useState('16:9')
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [providerConfigured, setProviderConfigured] = useState(false)
  const [apiAvailable, setApiAvailable] = useState(false)
  const fileRef = useRef(null)

  useEffect(() => {
    let active = true
    fetch(API + '/api/health')
      .then(response => response.ok ? response.json() : Promise.reject(new Error('API indisponible')))
      .then(data => {
        if (!active) return
        setApiAvailable(true)
        setProviderConfigured(Boolean(data.video_provider_configured))
      })
      .catch(() => {
        if (active) {
          setApiAvailable(false)
          setProviderConfigured(false)
        }
      })
    return () => { active = false }
  }, [])

  async function generate(e) {
    e.preventDefault()
    setNotice('')
    setVideoUrl('')
    if (prompt.trim().length < 3) {
      setNotice('Décris ta vidéo avec au moins quelques mots.')
      return
    }
    if (mode === 'image' && !file) {
      setNotice('Ajoute une image pour utiliser le mode Image vers vidéo.')
      return
    }
    if (Number(duration) > 10) {
      setNotice('Le moteur gratuit actuellement pris en charge limite chaque clip à 10 secondes. La génération multi-scènes pour 1 à 3 minutes n’est pas encore disponible.')
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
      if (!data.video_url) throw new Error('Le moteur n’a pas renvoyé de fichier vidéo. Aucun résultat ne sera simulé.')
      setVideoUrl(API + data.video_url)
      setNotice('Vidéo générée par le moteur connecté. Tu peux la lire ou la télécharger.')
    } catch (err) {
      setNotice(err.message || 'Erreur pendant la génération.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-icon"><Clapperboard size={21} /></span><span>motion<span className="brand-accent">lab</span><small>STUDIO IA</small></span></a><div className="top-actions"><span className="status-dot" /><span className="beta">BÊTA</span><a className="github-link" href="https://github.com/Leslie2856/generateur-video-ia" target="_blank" rel="noreferrer">GitHub ↗</a></div></header>
    <main id="top" className="main-grid">
      <section className="intro"><div className="eyebrow"><Sparkles size={14} /> TON IMAGINATION, EN MOUVEMENT</div><h1>Transforme tes idées<br />en <span>vidéos.</span></h1><p className="intro-copy">Décris une scène ou apporte une image. Génère de courts clips avec un moteur vidéo gratuit compatible.</p><div className="feature-row"><div><WandSparkles size={17}/><span>Texte en vidéo</span></div><div><ImagePlus size={17}/><span>Image en vidéo</span></div><div><Clock3 size={17}/><span>Clips jusqu’à 10 s</span></div></div><div className="preview-card"><div className="preview-orbit orbit-one"/><div className="preview-orbit orbit-two"/><div className="preview-center"><Clapperboard size={38}/><span>TON PROCHAIN FILM</span><small>COMMENCE ICI</small></div><div className="preview-chip chip-top">✦ Créativité sans limite</div><div className="preview-chip chip-bottom">FORMAT · {ratio}</div></div></section>
      <section className="studio-card"><div className="studio-heading"><div><div className="section-kicker">ESPACE DE CRÉATION</div><h2>Nouvelle vidéo</h2></div><span className="step-tag">01 <span>/ 03</span></span></div>
        <div className="mode-tabs"><button className={mode === 'text' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('text'); setNotice(''); setVideoUrl('') }} type="button"><WandSparkles size={17}/> Texte vers vidéo</button><button className={mode === 'image' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('image'); setNotice(''); setVideoUrl('') }} type="button"><ImagePlus size={17}/> Image vers vidéo</button></div>
        <form onSubmit={generate}><label className="field-label" htmlFor="prompt">DÉCRIS TA VIDÉO <span>REQUIS</span></label><textarea id="prompt" value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={4000} placeholder={mode === 'text' ? 'Ex. : Un coucher de soleil doré sur les dunes du Sahel, caméra qui avance lentement, style cinématographique…' : 'Ex. : Fais doucement avancer la caméra, ajoute un léger mouvement au vent et une lumière cinématographique…'} rows={5}/><div className="field-footer"><span>Un prompt précis donne une meilleure direction créative.</span><span>{prompt.length}/4000</span></div>
        {mode === 'image' && <div className="upload-zone" onClick={() => fileRef.current?.click()} role="button" tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileRef.current?.click() }}><input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e => { setFile(e.target.files?.[0] || null); setVideoUrl('') }}/><Upload size={22}/><strong>{file ? file.name : 'Choisir une image de départ'}</strong><span>PNG, JPG ou WebP · 10 Mo maximum</span></div>}
        <div className="settings-grid"><div><label className="field-label" htmlFor="duration">DURÉE</label><div className="select-wrap"><Clock3 size={16}/><select id="duration" value={duration} onChange={e => setDuration(Number(e.target.value))}>{[5,10,15,30,60,90,120,180].map(n => <option value={n} key={n} disabled={n > 10}>{n >= 60 ? (n / 60) + ' min' : n + ' secondes'}{n > 10 ? ' · bientôt' : ''}</option>)}</select></div></div><div><label className="field-label" htmlFor="ratio">FORMAT</label><div className="select-wrap"><MonitorPlay size={16}/><select id="ratio" value={ratio} onChange={e => setRatio(e.target.value)}><option value="16:9">16:9 · Paysage</option><option value="9:16">9:16 · Portrait</option><option value="1:1">1:1 · Carré</option></select></div></div></div>
        <div className="provider-note"><AlertCircle size={17}/><span><strong>{!apiAvailable ? 'API inaccessible' : providerConfigured ? 'Moteur vidéo configuré' : 'Moteur vidéo à configurer'}</strong> — {!apiAvailable ? 'Démarre le backend FastAPI puis réessaie.' : providerConfigured ? 'Le moteur gratuit est configuré. La disponibilité et le quota dépendent du Space choisi.' : 'Définis HF_VIDEO_SPACE_ID dans la configuration du backend. Aucun fournisseur payant ni basculement payant ne sera utilisé.'} Les clips de 1 à 3 minutes nécessitent encore un pipeline multi-scènes.</span></div>
        {notice && <div className="notice" role="status">{notice}</div>}
        <button className="generate-button" type="submit" disabled={busy}>{busy ? 'Génération en cours…' : <><Sparkles size={18}/> Générer ma vidéo <span>↗</span></>}</button><p className="fine-print">Une vidéo n’est affichée que si le moteur renvoie un vrai fichier.</p>
        {videoUrl && <div className="video-result"><video src={videoUrl} controls playsInline preload="metadata" /><a href={videoUrl} download><Download size={16}/> Télécharger la vidéo MP4</a></div>}
        </form>
      </section>
    </main><footer><span>motionlab · STUDIO IA</span><span>Génération gratuite uniquement · aucun recours payant</span></footer>
  </div>
}
