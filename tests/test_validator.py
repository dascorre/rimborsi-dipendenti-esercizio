from src import validator


def richiesta(**campi):
    base = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": 10.0,
        "giorni": 1,
        "km": None,
        "notti": None,
    }
    base.update(campi)
    return base


def test_richiesta_valida():
    assert validator.valida(richiesta()) == (True, "")


def test_dipendente_mancante():
    ok, motivazione = validator.valida(richiesta(dipendente=""))
    assert not ok
    assert motivazione == "dipendente mancante"


def test_categoria_non_riconosciuta():
    ok, motivazione = validator.valida(richiesta(categoria="parcheggio"))
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_importo_zero():
    ok, motivazione = validator.valida(richiesta(importo=0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_negativo():
    ok, motivazione = validator.valida(richiesta(importo=-5.0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_mancante():
    ok, motivazione = validator.valida(richiesta(importo=None))
    assert not ok
    assert motivazione == "importo non positivo"


def test_data_mancante():
    ok, motivazione = validator.valida(richiesta(data=""))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_data_non_valida():
    ok, motivazione = validator.valida(richiesta(data="06/10/2025"))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_giornate_mancanti_per_trasferta():
    ok, motivazione = validator.valida(
        richiesta(categoria="trasferta_italia", giorni=None)
    )
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_giornate_zero_per_pasto():
    ok, motivazione = validator.valida(richiesta(categoria="pasto", giorni=0))
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_chilometri_non_validi():
    ok, motivazione = validator.valida(
        richiesta(categoria="chilometrico", km=0)
    )
    assert not ok
    assert motivazione == "numero di chilometri non valido"


def test_notti_non_valide():
    ok, motivazione = validator.valida(
        richiesta(categoria="alloggio", notti=None)
    )
    assert not ok
    assert motivazione == "numero di notti non valido"


def test_chilometrico_valido():
    assert validator.valida(
        richiesta(categoria="chilometrico", km=120, giorni=None)
    ) == (True, "")


def test_alloggio_valido():
    assert validator.valida(
        richiesta(categoria="alloggio", notti=3, giorni=None)
    ) == (True, "")


# ---------------------------------------------------------------------------
# Test categoria lavoro_agile e regime transitorio
# ---------------------------------------------------------------------------

def _richiesta_valida_registrata(dipendente, categoria, data, giorni, importo=100.0):
    """Simula una richiesta già registrata come valida (per test incompatibilità)."""
    return {
        "dipendente": dipendente,
        "data": data,
        "categoria": categoria,
        "giorni": giorni,
        "importo": importo,
        "stato": "valida",
        "quota_esente": importo,
        "quota_imponibile": 0.0,
        "km": None,
        "notti": None,
    }


def test_lavoro_agile_valido():
    r = richiesta(categoria="lavoro_agile", data="2026-03-01", giorni=5)
    assert validator.valida(r) == (True, "")


def test_lavoro_agile_data_2025_respinto():
    r = richiesta(categoria="lavoro_agile", data="2025-12-01", giorni=5)
    ok, motivazione = validator.valida(r)
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_lavoro_agile_giornate_non_valide():
    r = richiesta(categoria="lavoro_agile", data="2026-03-01", giorni=0)
    ok, motivazione = validator.valida(r)
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_incompatibilita_agile_su_giorno_trasferta():
    # Trasferta dal 02/03 al 06/03 (5 gg), lavoro agile dal 06/03 al 08/03 → sovrapposizione
    esistenti = [_richiesta_valida_registrata("Maria Rossi", "trasferta_italia", "2026-03-02", 5)]
    r = richiesta(categoria="lavoro_agile", data="2026-03-06", giorni=3)
    ok, motivazione = validator.valida(r, richieste_esistenti=esistenti)
    assert not ok
    assert motivazione == "incompatibilità lavoro agile / trasferta"


def test_incompatibilita_trasferta_su_giorno_agile():
    # Lavoro agile sul 06/03, trasferta dal 02/03 al 06/03 → sovrapposizione
    esistenti = [_richiesta_valida_registrata("Maria Rossi", "lavoro_agile", "2026-03-06", 1)]
    r = richiesta(categoria="trasferta_italia", data="2026-03-02", giorni=5)
    ok, motivazione = validator.valida(r, richieste_esistenti=esistenti)
    assert not ok
    assert motivazione == "incompatibilità lavoro agile / trasferta"


def test_compatibilita_agile_senza_sovrapposizione():
    # Trasferta dal 02/03 al 05/03 (4 gg), lavoro agile dal 06/03 → nessuna sovrapposizione
    esistenti = [_richiesta_valida_registrata("Maria Rossi", "trasferta_italia", "2026-03-02", 4)]
    r = richiesta(categoria="lavoro_agile", data="2026-03-06", giorni=3)
    ok, _ = validator.valida(r, richieste_esistenti=esistenti)
    assert ok


def test_no_incompatibilita_se_richiesta_trasferta_e_respinta():
    # Una richiesta RESPINTA non deve creare incompatibilità
    trasferta_respinta = {
        "dipendente": "Maria Rossi",
        "data": "2026-03-02",
        "categoria": "trasferta_italia",
        "giorni": 5,
        "stato": "respinta",
    }
    r = richiesta(categoria="lavoro_agile", data="2026-03-06", giorni=3)
    ok, _ = validator.valida(r, richieste_esistenti=[trasferta_respinta])
    assert ok
