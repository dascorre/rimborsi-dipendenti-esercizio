"""Persistenza delle richieste su file JSON."""

import json
from datetime import date, timedelta
from pathlib import Path

PERCORSO_DATI = Path(__file__).resolve().parent.parent / "data" / "richieste.json"


def carica():
    if not PERCORSO_DATI.exists():
        return []
    with open(PERCORSO_DATI, encoding="utf-8") as f:
        return json.load(f)


def salva(richieste):
    PERCORSO_DATI.parent.mkdir(parents=True, exist_ok=True)
    with open(PERCORSO_DATI, "w", encoding="utf-8") as f:
        json.dump(richieste, f, ensure_ascii=False, indent=2)


def prossimo_id(richieste):
    return max((r["id"] for r in richieste), default=0) + 1


def mese(richiesta):
    """Mese di riferimento di una richiesta, nel formato AAAA-MM."""
    return richiesta["data"][:7]


def esente_riconosciuta_nel_mese(richieste, dipendente, mese_riferimento):
    """Somma delle quote esenti delle richieste valide del dipendente nel mese."""
    totale = sum(
        r["quota_esente"]
        for r in richieste
        if r["dipendente"] == dipendente
        and r["stato"] == "valida"
        and mese(r) == mese_riferimento
    )
    return round(totale, 2)


def giornate_lavoro_agile_nel_mese(richieste, dipendente, mese_riferimento):
    """Numero di giornate di lavoro agile già rimborsate al dipendente nel mese."""
    return sum(
        r["giorni"]
        for r in richieste
        if r["dipendente"] == dipendente
        and r["stato"] == "valida"
        and r["categoria"] == "lavoro_agile"
        and mese(r) == mese_riferimento
    )


def date_coperte(richiesta):
    """Set di date ISO coperte dalla richiesta (per categorie a giornate)."""
    giorni = richiesta.get("giorni")
    if not giorni or giorni <= 0:
        return set()
    inizio = date.fromisoformat(richiesta["data"])
    return {str(inizio + timedelta(days=i)) for i in range(giorni)}


def date_trasferta_valide(richieste, dipendente):
    """Set di tutte le date coperte da richieste valide di trasferta del dipendente."""
    result = set()
    for r in richieste:
        if (
            r["dipendente"] == dipendente
            and r["stato"] == "valida"
            and r["categoria"] in ("trasferta_italia", "trasferta_estero")
        ):
            result |= date_coperte(r)
    return result
