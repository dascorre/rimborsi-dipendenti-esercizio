from src import calculator


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


class TestMassimaleTeorico:
    def test_trasferta_italia(self):
        r = richiesta(categoria="trasferta_italia", giorni=4)
        assert calculator.massimale_teorico(r) == 185.92

    def test_trasferta_estero(self):
        r = richiesta(categoria="trasferta_estero", giorni=3)
        assert calculator.massimale_teorico(r) == 232.41

    def test_pasto(self):
        r = richiesta(categoria="pasto", giorni=5)
        assert calculator.massimale_teorico(r) == 40.0

    def test_chilometrico(self):
        r = richiesta(categoria="chilometrico", km=250)
        assert calculator.massimale_teorico(r) == 105.0

    def test_alloggio(self):
        r = richiesta(categoria="alloggio", notti=2)
        assert calculator.massimale_teorico(r) == 300.0


class TestCalcola:
    def test_importo_sotto_massimale_tutto_esente(self):
        r = richiesta(categoria="pasto", giorni=5, importo=35.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 35.0
        assert imponibile == 0.0

    def test_importo_sopra_massimale_eccedenza_imponibile(self):
        r = richiesta(categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 92.96
        assert imponibile == 27.04

    def test_plafond_incapiente_limita_la_quota_esente(self):
        r = richiesta(categoria="alloggio", notti=2, importo=300.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert esente == 100.0
        assert imponibile == 200.0

    def test_plafond_esaurito_tutto_imponibile(self):
        r = richiesta(categoria="pasto", giorni=1, importo=8.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1200.0)
        assert esente == 0.0
        assert imponibile == 8.0

    def test_dettaglio_del_calcolo(self):
        r = richiesta(categoria="trasferta_estero", giorni=2, importo=200.0)
        _, _, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert dettaglio == {
            "massimale_teorico": 154.94,
            "esente_teorica": 154.94,
            "capienza_plafond": 100.0,
        }


class TestMassimaleTeorico2026:
    """Verifica i massimali con regole MEF 18/2026 (data ≥ 2026-01-01)."""

    def test_trasferta_italia_2026(self):
        r = richiesta(categoria="trasferta_italia", giorni=4, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 200.00  # 50.00 × 4

    def test_trasferta_estero_2026_5_giorni_no_progressiva(self):
        r = richiesta(categoria="trasferta_estero", giorni=5, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 425.00  # 5 × 85.00

    def test_trasferta_estero_progressiva_6_giorni(self):
        r = richiesta(categoria="trasferta_estero", giorni=6, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 501.50  # 5×85 + 1×76.50

    def test_trasferta_estero_progressiva_12_giorni(self):
        r = richiesta(categoria="trasferta_estero", giorni=12, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 943.50  # 5×85 + 5×76.50 + 2×68

    def test_pasto_2026(self):
        r = richiesta(categoria="pasto", giorni=5, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 50.00  # 10.00 × 5

    def test_chilometrico_2026(self):
        r = richiesta(categoria="chilometrico", km=250, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 112.50  # 0.45 × 250

    def test_alloggio_2026(self):
        r = richiesta(categoria="alloggio", notti=2, data="2026-03-01")
        assert calculator.massimale_teorico(r) == 340.00  # 170.00 × 2

    def test_lavoro_agile_entro_limite(self):
        r = richiesta(categoria="lavoro_agile", giorni=6, data="2026-03-01")
        assert calculator.massimale_teorico(r, giornate_agile_nel_mese=0) == 21.00  # 3.50 × 6

    def test_lavoro_agile_giornate_eccedenti(self):
        r = richiesta(categoria="lavoro_agile", giorni=15, data="2026-03-01")
        assert calculator.massimale_teorico(r, giornate_agile_nel_mese=0) == 42.00  # 3.50 × 12

    def test_lavoro_agile_limite_parziale(self):
        r = richiesta(categoria="lavoro_agile", giorni=6, data="2026-03-01")
        assert calculator.massimale_teorico(r, giornate_agile_nel_mese=8) == 14.00  # 3.50 × 4


class TestCalcola2026:
    """Verifica il calcolo con plafond 2026 (1.400 €)."""

    def test_plafond_2026_capienza_residua(self):
        r = richiesta(categoria="pasto", giorni=5, importo=50.0, data="2026-03-01")
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1350.0)
        # capienza = 1400 - 1350 = 50; min(50, 50) = 50
        assert esente == 50.0
        assert imponibile == 0.0

    def test_plafond_2026_incapiente(self):
        r = richiesta(categoria="pasto", giorni=5, importo=50.0, data="2026-03-01")
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1380.0)
        # capienza = 1400 - 1380 = 20
        assert esente == 20.0
        assert imponibile == 30.0
