# Générateur vidéo IA

Application web de génération vidéo à partir d’un texte ou d’une image.

## Fonctionnalités de l’interface
- Modes **Texte vers vidéo** et **Image vers vidéo**
- Formats 9:16, 16:9 et 1:1
- Durée configurable de 5 secondes à 3 minutes
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

## Important : génération vidéo réelle
Le dépôt contient le socle de l’application, mais **aucun moteur de génération vidéo n’est encore connecté**. Les endpoints de génération répondent volontairement avec le statut HTTP 501 jusqu’à l’intégration d’un modèle ou d’un fournisseur vidéo compatible. Aucun résultat fictif n’est affiché comme une vidéo générée. Les coûts, limites de durée et besoins matériels dépendront du moteur choisi.

## Sécurité
Ne committez jamais de clés API, mots de passe ou fichiers `.env`. Utilisez des variables d’environnement pour les secrets.
