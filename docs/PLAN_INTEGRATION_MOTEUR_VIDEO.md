# Plan d'intégration du moteur vidéo — mode gratuit uniquement

## Contraintes confirmées

- Aucune modification de `main` et aucune fusion sans autorisation explicite.
- Développement sur `feature/video-engine-integration`.
- Coût utilisateur autorisé : **0**. Aucun appel payant, aucune recharge automatique, aucun basculement vers un fournisseur payant.
- Si le quota gratuit est épuisé ou que le service est saturé : mettre en attente ou arrêter proprement la génération.
- La durée demandée peut aller jusqu'à 180 secondes, sans supposer qu'un moteur sait générer 180 secondes en une seule requête.
- Le GPU local de l'utilisateur est inconnu.

## État constaté du dépôt avant intégration

- Le frontend React/Vite propose déjà le texte-vers-vidéo et l'image-vers-vidéo.
- L'API FastAPI expose `GET /api/health`, `POST /api/jobs` et `POST /api/jobs/image-to-video`.
- Les deux routes de génération répondent actuellement HTTP 501 ; aucun moteur vidéo réel n'est connecté.
- Les champs de durée autorisent 1 à 180 secondes côté API et plusieurs durées dans l'interface.
- Les dépendances backend actuelles sont minimales : FastAPI, Uvicorn, python-multipart et pydantic-settings.

## Évaluation de l'option gratuite

### Hugging Face Spaces / ZeroGPU

Candidat pour un prototype gratuit : les Spaces ZeroGPU existants sont accessibles gratuitement, avec une file d'attente et des quotas qui dépendent du compte. La documentation officielle indique actuellement un quota quotidien de GPU partagé pour les comptes gratuits. Le quota peut changer et la disponibilité n'est pas garantie.

Limites :
- Un Space public n'est pas une API de production garantie ; il peut être en veille, saturé, modifié ou indisponible.
- L'existence d'un Space ne garantit pas qu'il expose une API stable compatible avec le projet.
- Générer une vidéo finale de 3 minutes peut consommer beaucoup plus de temps GPU que le quota disponible.
- Il faut vérifier les conditions du Space précis et du modèle choisi avant de l'appeler depuis l'application.

### Hugging Face Inference Providers

La documentation officielle indique actuellement seulement 0,10 USD de crédits mensuels pour un compte gratuit, sous réserve de modification, puis des usages payants. Cette option n'est donc pas retenue comme solution de génération régulière dans une politique strictement gratuite. Aucun crédit ne doit être dépassé et aucun achat ne doit être déclenché.

### Génération locale (par exemple Wan 2.2)

À garder comme option ultérieure uniquement après vérification du matériel. La capacité GPU locale étant inconnue, ne pas l'imposer ni télécharger automatiquement un gros modèle.

## Architecture proposée

1. Créer une interface fournisseur côté backend afin de séparer l'API FastAPI du moteur choisi.
2. Ajouter une configuration explicite via variables d'environnement pour l'URL d'un Space choisi, sans clé ni URL codée en dur.
3. Faire échouer la génération avec un message clair si le fournisseur n'est pas configuré ; ne jamais produire une fausse vidéo.
4. Vérifier le quota / la disponibilité avant lancement lorsque l'API distante le permet.
5. Normaliser les statuts : `queued`, `running`, `succeeded`, `failed`, `quota_exhausted`.
6. En cas de saturation, conserver la tâche en attente ou arrêter avec une explication ; ne jamais utiliser une API payante en secours.
7. Pour une durée finale jusqu'à 180 secondes, prévoir un pipeline de scènes/segments, mais ne le mettre en œuvre qu'après confirmation des durées autorisées par le modèle retenu.
8. Vérifier le type et la taille des images reçues, les délais d'attente, les erreurs du fournisseur et les fichiers de sortie.
9. Ne jamais exposer les secrets dans le frontend, les réponses HTTP, les logs ou Git.

## Étapes de réalisation

- [x] Inspecter les fichiers existants avant modification.
- [x] Créer la branche isolée `feature/video-engine-integration` depuis `main`.
- [ ] Choisir et vérifier un Space/modèle gratuit précis, son API, sa licence, sa politique d'usage et ses limites.
- [ ] Implémenter un adaptateur backend désactivé par défaut.
- [ ] Ajouter une gestion de tâches et de quotas sans facturation.
- [ ] Connecter le frontend à l'état réel des tâches et aux résultats.
- [ ] Ajouter des tests avec fournisseur simulé pour les statuts et erreurs, sans présenter ces tests comme une génération réelle.
- [ ] Tester avec le fournisseur gratuit réel si le quota le permet.
- [ ] Mettre à jour le README et documenter explicitement les limites du gratuit.

## Garde-fous non négociables

- Aucun fournisseur payant.
- Aucun dépassement de quota volontaire.
- Aucun achat automatique ni facturation de secours.
- Aucun changement de `main`.
- Aucune fusion de branche ou création de pull request de fusion sans accord explicite.
- Ne pas annoncer la génération réelle tant qu'un test avec un moteur réel n'a pas réussi.
