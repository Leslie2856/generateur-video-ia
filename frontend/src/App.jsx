import { useEffect, useRef, useState } from 'react'
import { Clapperboard, ImagePlus, Sparkles, Upload, WandSparkles, Clock3, MonitorPlay, AlertCircle, Download, Film, Activity } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [mode, setMode] = useState('image')
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(3)
  const [ratio, setRatio] = useState('16:9')
  const [file, setFile] = useState(null)
  const [motionVideo, setMotionVideo] = useState(null)
  const [busy, setBusy] = useState(false)
  const [checking, setChecking] = useState(false)
  const [notice, setNotice] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [apiAvailable, setApiAvailable] = useState(false)
  const [providerStatus, setProviderStatus] = useState('')
  const fileRef = useRef(null)
  const motionVideoRef = useRef(null)

  useEffect(() => {
    let active = true
    fetch(API + '/api/health')
      .then(response => response.ok ? response.json() : Promise.reject(new Error('API indisponible')))
      .then(() => { if (active) setApiAvailable(true) })
      .catch(() => {
        if (active) {
          setApiAvailable(false)
          setProviderStatus('')
        }
      })
    return () => { active = false }
  }, [])

  async function checkProvider() {
    setChecking(true)
    setProviderStatus('')
    try {
      const response = await fetch(API + '/api/provider/health?mode=' + mode)
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(data.detail || 'Le Space gratuit est indisponible.')
      setProviderStatus('Connexion au Space réussie. Le quota GPU sera vérifié au lancement de la génération.')
    } catch (err) {
      setProviderStatus(err.message || 'Impossible de joindre le moteur gratuit.')
    } finally {
      setChecking(false)
    }
  }

  async function generate(e) {
    e.preventDefault()
    setNotice('')
    setVideoUrl('')
    if (prompt.trim().length < 3) {
      setNotice('Décris le mouvement ou la scène avec au moins quelques mots.')
      return
    }
    if (!file) {
      setNotice('Ajoute une image de personnage ou une image de départ.')
      return
    }
    if (mode === 'animate' && !motionVideo) {
      setNotice('Ajoute une courte vidéo qui servira de référence de mouvement.')
      return
    }
    if (mode === 'image' && Number(duration) > 5) {
      setNotice('Le moteur gratuit prend en charge au maximum 5 secondes par clip.')
      return
    }

    setBusy(true)
    try {
      const data = new FormData()
      data.append('prompt', prompt)
      data.append('image', file)
      let endpoint = '/api/jobs/image-to-video'
      if (mode === 'image') {
        data.append('duration_seconds', String(duration))
        data.append('aspect_ratio', ratio)
      } else {
        endpoint = '/api/jobs/animate'
        data.append('motion_video', motionVideo)
      }
      const response = await fetch(API + endpoint, { method: 'POST', body: data })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || 'La génération a échoué.')
      if (!result.video_url) throw new Error('Le moteur n’a pas renvoyé de fichier vidéo. Aucun résultat ne sera simulé.')
      setVideoUrl(API + result.video_url)
      setNotice('Le moteur gratuit a renvoyé une vidéo réelle. Tu peux la lire ou la télécharger.')
    } catch (err) {
      setNotice(err.message || 'Erreur pendant la génération.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-icon"><Clapperboard size={21} /></span><span>motion<span className="brand-accent">lab</span><small>STUDIO IA</small></span></a><div className="top-actions"><span className="status-dot" /><span className="beta">BÊTA</span><a className="github-link" href="https://github.com/Leslie2856/generateur-video-ia/tree/feature/video-engine-integration" target="_blank" rel="noreferrer">GitHub ↗</a></div></header>
    <main id="top" className="main-grid">
      <section className="intro"><div className="eyebrow"><Sparkles size={14} /> TON IMAGINATION, EN MOUVEMENT</div><h1>Transforme tes idées<br />en <span>vidéos.</span></h1><p className="intro-copy">Teste deux moteurs Wan 2.2 gratuits : animation d’une image ou transfert de mouvement à un personnage.</p><div className="feature-row"><div><ImagePlus size={17}/><span>Image en vidéo</span></div><div><Film size={17}/><span>Animation guidée</span></div><div><Clock3 size={17}/><span>Clips courts</span></div></div><div className="preview-card"><div className="preview-orbit orbit-one"/><div className="preview-orbit orbit-two"/><div className="preview-center"><Clapperboard size={38}/><span>TON PROCHAIN FILM</span><small>COMMENCE ICI</small></div><div className="preview-chip chip-top">✦ Wan 2.2 · ZeroGPU</div><div className="preview-chip chip-bottom">FORMAT · {ratio}</div></div></section>
      <section className="studio-card"><div className="studio-heading"><div><div className="section-kicker">ESPACE DE CRÉATION</div><h2>Nouvelle vidéo</h2></div><span className="step-tag">01 <span>/ 02</span></span></div>
        <div className="mode-tabs"><button className={mode === 'image' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('image'); setNotice(''); setProviderStatus(''); setVideoUrl('') }} type="button"><WandSparkles size={17}/> Image vers vidéo</button><button className={mode === 'animate' ? 'mode-tab active' : 'mode-tab'} onClick={() => { setMode('animate'); setNotice(''); setProviderStatus(''); setVideoUrl('') }} type="button"><Film size={17}/> Animer un personnage</button></div>
        <form onSubmit={generate}><label className="field-label" htmlFor="prompt">{mode === 'image' ? 'DÉCRIS LE MOUVEMENT À GÉNÉRER' : 'DÉCRIS LE RÉSULTAT SOUHAITÉ'} <span>REQUIS</span></label><textarea id="prompt" value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={4000} placeholder={mode === 'image' ? 'Ex. : Anime doucement cette image, vent dans les vêtements, caméra qui avance, lumière cinématographique…' : 'Ex. : Reproduis le mouvement de la vidéo de référence, en conservant l’apparence du personnage et le décor…'} rows={4}/><div className="field-footer"><span>Une consigne précise aide à guider le résultat.</span><span>{prompt.length}/4000</span></div>
        <div className="upload-zone" onClick={() => fileRef.current?.click()} role="button" tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileRef.current?.click() }}><input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={e => { setFile(e.target.files?.[0] || null); setVideoUrl('') }}/><ImagePlus size={22}/><strong>{file ? file.name : mode === 'image' ? 'Choisir une image de départ' : 'Choisir l’image du personnage'}</strong><span>PNG, JPG ou WebP · 10 Mo maximum</span></div>
        {mode === 'animate' && <div className="upload-zone" onClick={() => motionVideoRef.current?.click()} role="button" tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') motionVideoRef.current?.click() }}><input ref={motionVideoRef} type="file" accept="video/mp4,video/webm,video/quicktime" hidden onChange={e => { setMotionVideo(e.target.files?.[0] || null); setVideoUrl('') }}/><Upload size={22}/><strong>{motionVideo ? motionVideo.name : 'Choisir la vidéo de mouvement'}</strong><span>MP4, WebM ou MOV · 25 Mo maximum</span></div>}
        {mode === 'image' && <div className="settings-grid"><div><label className="field-label" htmlFor="duration">DURÉE DU CLIP</label><div className="select-wrap"><Clock3 size={16}/><select id="duration" value={duration} onChange={e => setDuration(Number(e.target.value))}>{[2,3,4,5].map(n => <option value={n} key={n}>{n} secondes</option>)}</select></div></div><div><label className="field-label" htmlFor="ratio">FORMAT</label><div className="select-wrap"><MonitorPlay size={16}/><select id="ratio" value={ratio} onChange={e => setRatio(e.target.value)}><option value="16:9">16:9 · Paysage</option><option value="9:16">9:16 · Portrait</option><option value="1:1">1:1 · Carré</option></select></div></div></div>}
        <div className="provider-note"><AlertCircle size={17}/><span><strong>{!apiAvailable ? 'API inaccessible' : mode === 'image' ? 'Wan2.2 Image-to-Video' : 'Wan2.2 Animate-2'}</strong> — {!apiAvailable ? 'Démarre le backend FastAPI puis réessaie.' : mode === 'image' ? 'Anime une image de départ via un Space public ZeroGPU.' : 'Utilise une image de personnage et une vidéo de mouvement.'} Les quotas gratuits et les files d’attente dépendent de Hugging Face. Aucun fournisseur payant ne sera appelé.</span></div>
        <button className="mode-tab" type="button" onClick={checkProvider} disabled={!apiAvailable || checking}><Activity size={16}/>{checking ? 'Test de connexion…' : 'Tester la connexion au moteur'}</button>
        {providerStatus && <div className="notice" role="status">{providerStatus}</div>}
        {notice && <div className="notice" role="status">{notice}</div>}
        <button className="generate-button" type="submit" disabled={busy}>{busy ? 'Génération en cours…' : <><Sparkles size={18}/> Générer ma vidéo <span>↗</span></>}</button><p className="fine-print">La génération peut prendre plusieurs minutes. Une vidéo n’est affichée que si le moteur renvoie un vrai fichier.</p>
        {videoUrl && <div className="video-result"><video src={videoUrl} controls playsInline preload="metadata" /><a href={videoUrl} download><Download size={16}/> Télécharger la vidéo MP4</a></div>}
        </form>
      </section>
    </main><footer><span>motionlab · STUDIO IA</span><span>Génération gratuite uniquement · aucun recours payant</span></footer>
  </div>
}
