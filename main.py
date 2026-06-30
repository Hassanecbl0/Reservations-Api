from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import uuid
from datetime import datetime
from pathlib import Path

app = FastAPI(title="STAF Reservation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path("database.json")


def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Modèles ----------

class ReservationRequest(BaseModel):
    trajet_id: str
    nom_client: str
    telephone: str
    nombre_places: Optional[int] = 1

class AnnulationRequest(BaseModel):
    reservation_id: str


# ---------- Routes ----------

@app.get("/")
def root():
    return {"message": "STAF Reservation API", "status": "ok"}


@app.get("/trajets")
def lister_trajets(depart: Optional[str] = None, arrivee: Optional[str] = None, date: Optional[str] = None):
    """
    Liste les trajets disponibles.
    Paramètres optionnels : depart, arrivee, date (YYYY-MM-DD)
    Utilisé par l'agent ElevenLabs pour annoncer les horaires.
    """
    db = load_db()
    trajets = db["trajets"]

    if depart:
        trajets = [t for t in trajets if depart.lower() in t["depart"].lower()]
    if arrivee:
        trajets = [t for t in trajets if arrivee.lower() in t["arrivee"].lower()]
    if date:
        trajets = [t for t in trajets if t["date"] == date]

    trajets_disponibles = [t for t in trajets if t["places_disponibles"] > 0]

    if not trajets_disponibles:
        return {
            "status": "aucun_trajet",
            "message": "Aucun trajet disponible pour cette recherche.",
            "trajets": []
        }

    return {
        "status": "ok",
        "nombre": len(trajets_disponibles),
        "trajets": [
            {
                "id": t["id"],
                "depart": t["depart"],
                "arrivee": t["arrivee"],
                "date": t["date"],
                "heure": t["heure"],
                "prix": t["prix"],
                "places_disponibles": t["places_disponibles"],
                "bus": t["bus"]
            }
            for t in trajets_disponibles
        ]
    }


@app.post("/reserver")
def reserver(req: ReservationRequest):
    """
    Réserve une ou plusieurs places sur un trajet.
    Appelé par l'agent ElevenLabs après confirmation du client.
    Décrémente automatiquement les places disponibles.
    """
    db = load_db()

    trajet = next((t for t in db["trajets"] if t["id"] == req.trajet_id), None)
    if not trajet:
        raise HTTPException(status_code=404, detail="Trajet introuvable.")

    if trajet["places_disponibles"] < req.nombre_places:
        return {
            "status": "echec",
            "message": f"Seulement {trajet['places_disponibles']} place(s) disponible(s) sur ce trajet."
        }

    # Décrémenter les places
    trajet["places_disponibles"] -= req.nombre_places

    # Créer la réservation
    reservation = {
        "id": str(uuid.uuid4())[:8].upper(),
        "trajet_id": req.trajet_id,
        "depart": trajet["depart"],
        "arrivee": trajet["arrivee"],
        "date": trajet["date"],
        "heure": trajet["heure"],
        "bus": trajet["bus"],
        "nom_client": req.nom_client,
        "telephone": req.telephone,
        "nombre_places": req.nombre_places,
        "prix_total": trajet["prix"] * req.nombre_places,
        "cree_le": datetime.now().isoformat()
    }

    db["reservations"].append(reservation)
    save_db(db)

    return {
        "status": "confirme",
        "message": f"Réservation confirmée ! Votre numéro de billet est {reservation['id']}.",
        "reservation": reservation
    }


@app.get("/reservation/{reservation_id}")
def consulter_reservation(reservation_id: str):
    """
    Consulte une réservation existante par son ID.
    """
    db = load_db()
    reservation = next((r for r in db["reservations"] if r["id"] == reservation_id), None)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    return {"status": "ok", "reservation": reservation}


@app.post("/annuler")
def annuler_reservation(req: AnnulationRequest):
    """
    Annule une réservation et restitue les places dans le bus.
    """
    db = load_db()

    reservation = next((r for r in db["reservations"] if r["id"] == req.reservation_id), None)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")

    # Restituer les places
    trajet = next((t for t in db["trajets"] if t["id"] == reservation["trajet_id"]), None)
    if trajet:
        trajet["places_disponibles"] += reservation["nombre_places"]

    db["reservations"] = [r for r in db["reservations"] if r["id"] != req.reservation_id]
    save_db(db)

    return {
        "status": "annule",
        "message": f"Réservation {req.reservation_id} annulée avec succès."
    }


@app.get("/reservations")
def lister_reservations():
    """
    Liste toutes les réservations (usage interne / admin).
    """
    db = load_db()
    return {"status": "ok", "reservations": db["reservations"]}
