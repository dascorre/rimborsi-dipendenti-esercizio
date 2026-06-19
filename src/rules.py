"""Parametri normativi per il calcolo dei rimborsi spese.

Fonte corrente: Circolare MEF n. 18/2026, in vigore per l'anno 2026.
Fonte previgente: Circolare MEF n. 41/2024, applicabile alle spese fino al 31/12/2025.
"""

# Parametri previgenti – Circolare MEF n. 41/2024 (spese con data ≤ 31/12/2025)
REGOLE_2025 = {
    "massimali_giornalieri": {
        "trasferta_italia": 46.48,
        "trasferta_estero": 77.47,
        "pasto": 8.00,
    },
    "massimale_km": 0.42,
    "massimale_notte": 150.00,
    "plafond_mensile": 1200.00,
    "max_giorni_lavoro_agile": 0,
    "progressiva_estero": False,
}

# Parametri vigenti – Circolare MEF n. 18/2026 (spese con data ≥ 01/01/2026)
REGOLE_2026 = {
    "massimali_giornalieri": {
        "trasferta_italia": 50.00,
        "trasferta_estero": 85.00,
        "pasto": 10.00,
        "lavoro_agile": 3.50,
    },
    "massimale_km": 0.45,
    "massimale_notte": 170.00,
    "plafond_mensile": 1400.00,
    "max_giorni_lavoro_agile": 12,
    "progressiva_estero": True,
}

DATA_DECORRENZA_2026 = "2026-01-01"


def regole_per_data(data_str):
    """Restituisce il set di regole applicabile alla data di sostenimento indicata."""
    return REGOLE_2026 if data_str >= DATA_DECORRENZA_2026 else REGOLE_2025


# Costanti flat ai valori 2026 – usate dal template /normativa e per compatibilità
MASSIMALI_GIORNALIERI = REGOLE_2026["massimali_giornalieri"]
MASSIMALE_KM = REGOLE_2026["massimale_km"]
MASSIMALE_NOTTE = REGOLE_2026["massimale_notte"]
PLAFOND_MENSILE = REGOLE_2026["plafond_mensile"]

CATEGORIE = {
    "trasferta_italia": "Trasferta in Italia",
    "trasferta_estero": "Trasferta all'estero",
    "pasto": "Rimborso pasto",
    "chilometrico": "Rimborso chilometrico",
    "alloggio": "Rimborso alloggio",
    "lavoro_agile": "Indennità lavoro agile",
}

CATEGORIE_A_GIORNATE = ("trasferta_italia", "trasferta_estero", "pasto", "lavoro_agile")

RIFERIMENTO_NORMATIVO = "Circolare MEF n. 18/2026"
