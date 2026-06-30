# STAF Reservation API — Guide de déploiement

## 1. Déploiement sur Render (gratuit)

### Étapes

1. Crée un compte sur [render.com](https://render.com)
2. Nouveau service → **Web Service**
3. Connecte ton repo GitHub contenant ces fichiers
4. Configure :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment** : Python 3
5. Clique **Deploy** — Render te donnera une URL publique du type :
   `https://staf-api.onrender.com`

---

## 2. Tester l'API localement

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Ouvre : http://localhost:8000/docs (documentation interactive automatique)

---

## 3. Routes disponibles

| Méthode | Route | Description |
|--------|-------|-------------|
| GET | `/trajets` | Liste les trajets disponibles |
| GET | `/trajets?depart=Ouaga&arrivee=Bobo` | Filtrer par ville |
| POST | `/reserver` | Créer une réservation |
| GET | `/reservation/{id}` | Consulter une réservation |
| POST | `/annuler` | Annuler une réservation |
| GET | `/reservations` | Toutes les réservations (admin) |

---

## 4. Configuration de l'agent ElevenLabs

### Dans ElevenLabs → Conversational AI → ton agent → Tools

#### Outil 1 : Chercher les trajets
- **Nom** : `chercher_trajets`
- **Type** : Webhook (GET)
- **URL** : `https://staf-api.onrender.com/trajets`
- **Paramètres** :
  - `depart` (string) — ville de départ
  - `arrivee` (string) — ville d'arrivée
  - `date` (string) — date au format YYYY-MM-DD

#### Outil 2 : Réserver une place
- **Nom** : `reserver_place`
- **Type** : Webhook (POST)
- **URL** : `https://staf-api.onrender.com/reserver`
- **Body (JSON)** :
```json
{
  "trajet_id": "{{trajet_id}}",
  "nom_client": "{{nom_client}}",
  "telephone": "{{telephone}}",
  "nombre_places": "{{nombre_places}}"
}
```

#### Outil 3 : Annuler une réservation
- **Nom** : `annuler_reservation`
- **Type** : Webhook (POST)
- **URL** : `https://staf-api.onrender.com/annuler`
- **Body (JSON)** :
```json
{
  "reservation_id": "{{reservation_id}}"
}
```

---

## 5. Prompt système pour l'agent ElevenLabs

```
Tu es l'agent vocal de STAF (Société de Transport Aorèma et Frères), 
une compagnie de transport au Burkina Faso.

Tu peux communiquer en français, en anglais et en mooré selon la langue du client.

Ton rôle :
1. Accueillir le client chaleureusement
2. Demander sa ville de départ, d'arrivée et la date souhaitée
3. Appeler l'outil "chercher_trajets" pour obtenir les horaires disponibles
4. Annoncer clairement les horaires, prix et places disponibles
5. Demander confirmation du trajet choisi
6. Collecter : nom complet et numéro de téléphone
7. Appeler l'outil "reserver_place" pour finaliser la réservation
8. Communiquer le numéro de billet au client
9. En cas d'annulation, utiliser "annuler_reservation" avec le numéro de billet

Sois toujours poli, clair et patient.
Si aucun trajet n'est disponible, propose des alternatives (autre horaire ou date).
```

---

## 6. Ajouter de nouveaux trajets

Modifie directement le fichier `database.json` en ajoutant un objet dans le tableau `trajets` :

```json
{
  "id": "T007",
  "depart": "Ouagadougou",
  "arrivee": "Fada N'Gourma",
  "date": "2026-07-01",
  "heure": "09:00",
  "prix": 4000,
  "places_total": 35,
  "places_disponibles": 35,
  "bus": "BUS-D1"
}
```
