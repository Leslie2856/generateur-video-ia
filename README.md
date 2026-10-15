# Générateur vidéo IA

Application web de génération vidéo à partir d’un texte ou d’une image.

## Fonctionnalités de l’interface
- Modes **Texte vers vidéo** et **Image vers vidéo**
- Formats 9:16, 16:9 et 1:1
- Clips de 5 secondes avec le moteur gratuit actuel (assemblage 1–3 minutes à développer)
- Interface React/Vite responsive en français
- API Python/FastAPI avec endpoint de santé et endpoints de génération préparés

## Architecture
- `frontend/` : interface React avec Vite
- `backend/app/main.py` : API FastAPI
- `backend/requirements.txt` : dépendances Python

## Lancer en local

### 1. Backend (terminal 1)
Depuis la racine du dépôt :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend --port 8000
```

API : http://127.0.0.1:8000  
Documentation interactive : http://127.0.0.1:8000/docs

### 2. Frontend (terminal 2)
Depuis la racine du dépôt :

```powershell
cd frontend
npm install
npm run dev
```

Ouvre ensuite l’adresse affichée par Vite, généralement http://localhost:5173.

## Génération vidéo réelle — fournisseur gratuit uniquement

L'API utilise l'adaptateur Gradio de l'espace public **Wan-AI/Wan-2.2-5B** sur Hugging Face ZeroGPU. Le backend ne transmet aucun jeton d'accès et ne propose aucun fournisseur payant de secours. Si le Space est en veille, saturé, indisponible ou si le quota gratuit est atteint, la génération échoue avec un message explicite ; réessayez plus tard.

- Les clips sont limités à **5 secondes** par requête avec ce modèle.
- Les comptes Hugging Face gratuits ont un quota GPU quotidien limité et les files d'attente peuvent varier. Comme le client n'utilise pas de jeton, le quota anonyme, plus faible, peut s'appliquer.
- Les vidéos finales de **1 à 3 minutes ne sont pas encore prises en charge** : il faudra implémenter l'assemblage multi-scènes, puis valider que les quotas gratuits le permettent.
- L'interface affiche et permet de télécharger un MP4 uniquement si le fournisseur renvoie un vrai fichier.
- Le Space public peut changer ou s'arrêter ; la disponibilité de ce service tiers n'est pas garantie.

Références : [Space Wan 2.2 ZeroGPU](https://huggingface.co/spaces/Wan-AI/Wan-2.2-5B) · [Quotas ZeroGPU officiels](https://huggingface.co/docs/hub/en/spaces-zerogpu) · [API des Spaces Gradio](https://huggingface.co/docs/hub/en/spaces-api-endpoints)

## Tests

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

Les tests backend utilisent un fournisseur simulé uniquement pour vérifier les routes, les limites et les erreurs. Ils ne consomment pas de quota ZeroGPU et ne prétendent pas prouver qu'une génération distante réelle a réussi. Pour tester le vrai moteur, lancez l'application puis envoyez un prompt de 5 secondes ; ce test consommera le quota gratuit du Space.

## Configuration du moteur

Aucune clé API n'est requise ou acceptée par cette intégration. Le Space public par défaut est défini dans `backend/app/video_provider.py`. Aucun jeton Hugging Face ne doit être ajouté au frontend ou aux fichiers de configuration.

## Sécurité
Ne committez jamais de clés API, mots de passe ou fichiers `.env`. Utilisez des variables d’environnement pour les secrets.
