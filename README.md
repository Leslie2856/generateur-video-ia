# Générateur vidéo IA

Application web React/FastAPI pour tester deux modèles Wan 2.2 hébergés sur des Spaces publics Hugging Face ZeroGPU.

## Fonctionnalités disponibles dans cette branche

- **Image vers vidéo** avec Wan2.2-I2V-A14B via un Space public ZeroGPU.
- **Animation de personnage** avec Wan2.2 Animate-2 : image du personnage + courte vidéo de mouvement + consigne textuelle.
- Lecture et téléchargement du MP4 renvoyé par le moteur.
- Test de connexion aux Spaces depuis l’interface.
- Réponses explicites si le Space est indisponible ou si le quota gratuit est atteint.
- Aucun jeton Hugging Face requis ou transmis ; aucun fournisseur payant de secours.
- Le mode **texte seul vers vidéo n’est pas disponible** dans cette intégration, car les deux modèles retenus ont besoin d’une image.

## Architecture

- `frontend/` : interface React/Vite en français.
- `backend/app/main.py` : API FastAPI et validation des fichiers.
- `backend/app/video_provider.py` : adaptateurs Gradio pour les deux Spaces.
- `backend/tests/` : tests des routes avec moteurs simulés (sans consommation de quota GPU).

## Lancer en local sous Windows

### 1. Backend — terminal PowerShell n° 1

Depuis la racine du dépôt :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend --port 8000
```

API : http://127.0.0.1:8000  
Documentation interactive : http://127.0.0.1:8000/docs

### 2. Frontend — terminal PowerShell n° 2

Depuis la racine du dépôt :

```powershell
cd frontend
npm install
npm run dev
```

Ouvre l’adresse affichée par Vite, généralement http://localhost:5173.

Si PowerShell ne reconnaît pas `npm`, installe Node.js LTS puis ferme et rouvre le terminal. Vérifie avec `node -v` et `npm -v`.

## Comment tester

### Test A — Image vers vidéo

1. Lance le backend et le frontend.
2. Dans l’application, choisis **Image vers vidéo**.
3. Charge une image JPG, PNG ou WebP de 10 Mo maximum.
4. Saisis une consigne de mouvement.
5. Choisis une durée courte (2 à 5 secondes) et clique sur **Générer ma vidéo**.
6. Attends la fin de la file ZeroGPU ; si le moteur renvoie un MP4, il s’affiche et peut être téléchargé.

Space utilisé : [Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom](https://huggingface.co/spaces/Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom). Il utilise une version quantifiée et optimisée de Wan2.2 I2V, basée sur le modèle Wan2.2-I2V-A14B. Le Space et son API peuvent évoluer indépendamment de ce dépôt.

### Test B — Animer un personnage

1. Choisis **Animer un personnage**.
2. Charge l’image de référence du personnage (10 Mo maximum).
3. Charge une courte vidéo qui montre le mouvement à reproduire (MP4, WebM ou MOV, 25 Mo maximum).
4. Décris le résultat souhaité et lance la génération.

Space utilisé : [hugging-apps/wan2-2-animate-2-14b](https://huggingface.co/spaces/hugging-apps/wan2-2-animate-2-14b). L’API publique expose l’endpoint Gradio `/animate`.

### Vérifier la connexion

Le bouton **Tester la connexion au moteur** vérifie que le client peut initialiser le Space sélectionné. Cela ne garantit pas que le GPU soit disponible ni que la génération aboutira ; la requête réelle peut toujours être mise en attente ou refusée par le quota.

## Limites gratuites et transparence

- La génération vidéo consomme le quota GPU gratuit du Space public. Les files, quotas et périodes de disponibilité sont contrôlés par Hugging Face et le propriétaire du Space.
- L’intégration n’envoie pas de jeton Hugging Face et ne bascule jamais vers une API payante. Si le quota est épuisé, attends son renouvellement ou réessaie plus tard.
- Les clips image-vers-vidéo sont limités à 5 secondes dans l’interface de cette version pour faciliter les premiers tests. Le Space Animate a ses propres limites de durée et de taille de fichiers.
- La génération de vidéos de 1 à 3 minutes par assemblage multi-scènes n’est pas encore implémentée.
- L’exécution locale des poids A14B demanderait une très grande mémoire GPU ; l’application s’appuie donc sur des Spaces hébergés, pas sur le GPU de ton ordinateur.
- Le statut « Space joignable » n’est pas une garantie de génération réussie. Seul un fichier MP4 réel reçu et validé est affiché.

## Tests automatisés

Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python -m pytest -q
cd ..\frontend
npm install
npm run build
```

Les tests utilisent des fournisseurs simulés : ils vérifient les routes, les validations et les erreurs, sans consommer de quota ZeroGPU. Ils ne remplacent pas un essai réel sur les Spaces publics.

## Références

- [Modèle Wan2.2-I2V-A14B](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B)
- [Modèle Wan2.2-Animate-2-14B](https://huggingface.co/Wan-AI/Wan2.2-Animate-2-14B)
- [API des Spaces Gradio](https://huggingface.co/docs/hub/en/spaces-api-endpoints)
- [Quotas et fonctionnement ZeroGPU](https://huggingface.co/docs/hub/en/spaces-zerogpu)

## Sécurité

Ne committe jamais de clés API, mots de passe ou fichiers `.env`. Aucun secret n’est nécessaire pour cette intégration publique gratuite.
