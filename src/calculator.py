"""Calcolo della quota esente e della quota imponibile di una richiesta."""

from src import rules


def _massimale_trasferta_estero_progressiva(giorni):
    """Massimale teorico per trasferta estera con riduzione progressiva (Sez. 4, MEF 18/2026).

    - gg 1-5:  85,00 € (pieno)
    - gg 6-10: 76,50 € (−10%)
    - gg 11+:  68,00 € (−20%)
    """
    g1 = min(giorni, 5)
    g2 = min(max(giorni - 5, 0), 5)
    g3 = max(giorni - 10, 0)
    return round(g1 * 85.00 + g2 * 76.50 + g3 * 68.00, 2)


def _massimale_lavoro_agile(giorni, giornate_gia_usate, regole):
    """Massimale teorico per lavoro agile, tenendo conto del limite mensile di 12 gg."""
    ammesse = min(giorni, max(regole["max_giorni_lavoro_agile"] - giornate_gia_usate, 0))
    return round(regole["massimali_giornalieri"]["lavoro_agile"] * ammesse, 2)


def massimale_teorico(richiesta, giornate_agile_nel_mese=0):
    """Massimale di esenzione applicabile alla richiesta, in base alla categoria e alla data."""
    categoria = richiesta["categoria"]
    regole = rules.regole_per_data(richiesta["data"])

    if categoria == "lavoro_agile":
        return _massimale_lavoro_agile(richiesta["giorni"], giornate_agile_nel_mese, regole)
    if categoria == "trasferta_estero":
        if regole["progressiva_estero"] and richiesta["giorni"] > 5:
            return _massimale_trasferta_estero_progressiva(richiesta["giorni"])
        return round(regole["massimali_giornalieri"]["trasferta_estero"] * richiesta["giorni"], 2)
    if categoria in rules.CATEGORIE_A_GIORNATE:
        return round(regole["massimali_giornalieri"][categoria] * richiesta["giorni"], 2)
    if categoria == "chilometrico":
        return round(regole["massimale_km"] * richiesta["km"], 2)
    if categoria == "alloggio":
        return round(regole["massimale_notte"] * richiesta["notti"], 2)
    raise ValueError(f"categoria non gestita: {categoria}")


def calcola(richiesta, esente_gia_riconosciuta, giornate_agile_nel_mese=0):
    """Restituisce (quota_esente, quota_imponibile, dettaglio).

    `esente_gia_riconosciuta` è la quota esente già riconosciuta al dipendente
    nel mese della richiesta, ai fini del plafond mensile.
    `giornate_agile_nel_mese` è il numero di giornate di lavoro agile già
    rimborsate al dipendente nel mese (usato solo per la categoria lavoro_agile).
    """
    regole = rules.regole_per_data(richiesta["data"])
    importo = richiesta["importo"]
    teorico = massimale_teorico(richiesta, giornate_agile_nel_mese)
    esente_teorica = min(importo, teorico)
    capienza = max(regole["plafond_mensile"] - esente_gia_riconosciuta, 0.0)
    esente = round(min(esente_teorica, capienza), 2)
    imponibile = round(importo - esente, 2)
    dettaglio = {
        "massimale_teorico": teorico,
        "esente_teorica": round(esente_teorica, 2),
        "capienza_plafond": round(capienza, 2),
    }
    return esente, imponibile, dettaglio
