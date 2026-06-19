import pytest

from src import storage
from src.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "PERCORSO_DATI", tmp_path / "richieste.json")
    app.config["TESTING"] = True
    return app.test_client()


def nuova_richiesta_pasto(client, **campi):
    dati = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": "24.00",
        "giorni": "3",
    }
    dati.update(campi)
    return client.post("/nuova", data=dati)


def test_home_reindirizza_a_elenco(client):
    risposta = client.get("/")
    assert risposta.status_code == 302
    assert "/richieste" in risposta.headers["Location"]


def test_pagine_principali_raggiungibili(client):
    for percorso in ("/richieste", "/nuova", "/riepilogo", "/normativa"):
        assert client.get(percorso).status_code == 200


def test_registrazione_richiesta_valida(client):
    risposta = nuova_richiesta_pasto(client)
    assert risposta.status_code == 200
    assert "registrata" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert len(richieste) == 1
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 0.0


def test_registrazione_richiesta_respinta(client):
    risposta = nuova_richiesta_pasto(client, importo="-10")
    assert "respinta" in risposta.get_data(as_text=True)
    assert "importo non positivo" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert richieste[0]["stato"] == "respinta"
    assert richieste[0]["quota_esente"] == 0.0


def test_eccedenza_oltre_massimale_diventa_imponibile(client):
    nuova_richiesta_pasto(client, importo="30.00", giorni="3")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 6.0


def test_plafond_mensile_condiviso_tra_richieste(client):
    nuova_richiesta_pasto(
        client, categoria="alloggio", notti="8", importo="1150.00", giorni=""
    )
    nuova_richiesta_pasto(client, importo="80.00", giorni="10")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1150.0
    # Capienza residua: 1200 - 1150 = 50, quindi del pasto sono esenti solo 50.
    assert richieste[1]["quota_esente"] == 50.0
    assert richieste[1]["quota_imponibile"] == 30.0


def test_elenco_filtra_per_dipendente(client):
    nuova_richiesta_pasto(client, dipendente="Maria Rossi")
    nuova_richiesta_pasto(client, dipendente="Luca Bianchi")
    testo = client.get("/richieste?dipendente=Luca+Bianchi").get_data(as_text=True)
    assert "Luca Bianchi" in testo
    assert "Maria Rossi" not in testo.split("</thead>")[1].split("Clicca")[0]


def test_riepilogo_mostra_totali(client):
    nuova_richiesta_pasto(client)
    nuova_richiesta_pasto(client, importo="16.00", giorni="2")
    testo = client.get("/riepilogo").get_data(as_text=True)
    assert "Maria Rossi" in testo
    assert "40.00" in testo


def test_normativa_mostra_massimali_vigenti(client):
    testo = client.get("/normativa").get_data(as_text=True)
    assert "50.00" in testo    # trasferta_italia 2026
    assert "85.00" in testo    # trasferta_estero 2026
    assert "1400.00" in testo  # plafond 2026
    assert "3.50" in testo     # lavoro_agile 2026


# ---------------------------------------------------------------------------
# Test regime transitorio
# ---------------------------------------------------------------------------

def test_transitorio_richiesta_2025_usa_massimali_vecchi(client):
    # Pasto 3 gg con data 2025: massimale 2025 = 8,00/gg → 24,00; con 2026 sarebbe 30,00
    nuova_richiesta_pasto(client, importo="30.00", giorni="3")  # data default 2025-10-06
    richieste = storage.carica()
    assert richieste[0]["dettaglio"]["massimale_teorico"] == 24.0
    assert richieste[0]["quota_imponibile"] == 6.0


# ---------------------------------------------------------------------------
# Test plafond 2026 (1.400 €)
# ---------------------------------------------------------------------------

def test_plafond_2026_1400(client):
    # Prima richiesta: alloggio 8 notti data 2026 → esente = min(1360, 1400) = 1360
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-01",
        "categoria": "alloggio",
        "importo": "1360.00",
        "notti": "8",
    })
    # Seconda richiesta: pasto 5 gg → capienza residua = 1400 - 1360 = 40
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-01",
        "categoria": "pasto",
        "importo": "50.00",
        "giorni": "5",
    })
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1360.0
    assert richieste[1]["quota_esente"] == 40.0
    assert richieste[1]["quota_imponibile"] == 10.0


# ---------------------------------------------------------------------------
# Test categoria lavoro_agile
# ---------------------------------------------------------------------------

def test_lavoro_agile_registrato_correttamente(client):
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-01",
        "categoria": "lavoro_agile",
        "importo": "21.00",
        "giorni": "6",
    })
    richieste = storage.carica()
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 21.0   # 3.50 × 6 = 21.00
    assert richieste[0]["quota_imponibile"] == 0.0


def test_lavoro_agile_respinto_per_incompatibilita(client):
    # Prima registra una trasferta valida dal 10 al 12 marzo
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-10",
        "categoria": "trasferta_italia",
        "importo": "50.00",
        "giorni": "3",
    })
    # Poi lavoro agile il 10 marzo (giornata sovrapposta)
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-10",
        "categoria": "lavoro_agile",
        "importo": "3.50",
        "giorni": "1",
    })
    richieste = storage.carica()
    assert richieste[1]["stato"] == "respinta"
    assert richieste[1]["motivazione"] == "incompatibilità lavoro agile / trasferta"


# ---------------------------------------------------------------------------
# Test trasferta estera con progressiva
# ---------------------------------------------------------------------------

def test_trasferta_estera_progressiva(client):
    client.post("/nuova", data={
        "dipendente": "Maria Rossi",
        "data": "2026-03-01",
        "categoria": "trasferta_estero",
        "importo": "1100.00",
        "giorni": "12",
    })
    richieste = storage.carica()
    # Massimale = 5×85 + 5×76.50 + 2×68 = 425 + 382.50 + 136 = 943.50
    assert richieste[0]["dettaglio"]["massimale_teorico"] == 943.50
    assert richieste[0]["quota_esente"] == 943.50
    assert richieste[0]["quota_imponibile"] == 156.50
