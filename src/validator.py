"""Regole di validazione delle richieste di rimborso."""

from datetime import date

from src import rules, storage


def valida(richiesta, richieste_esistenti=None):
    """Restituisce (True, "") se la richiesta è valida, altrimenti (False, motivazione).

    `richieste_esistenti` è la lista delle richieste già registrate; se fornito,
    viene effettuato anche il controllo di incompatibilità lavoro agile / trasferta
    (Sez. 5, Circ. MEF n. 18/2026).
    """
    if not richiesta.get("dipendente"):
        return False, "dipendente mancante"

    categoria = richiesta.get("categoria")
    if categoria not in rules.CATEGORIE:
        return False, "categoria non riconosciuta"

    importo = richiesta.get("importo")
    if importo is None or importo <= 0:
        return False, "importo non positivo"

    data = richiesta.get("data") or ""
    try:
        date.fromisoformat(data)
    except ValueError:
        return False, "data mancante o non valida"

    # La categoria lavoro_agile è ammessa solo per spese con data dal 01/01/2026
    if categoria == "lavoro_agile" and data < rules.DATA_DECORRENZA_2026:
        return False, "categoria non riconosciuta"

    if categoria in rules.CATEGORIE_A_GIORNATE:
        giorni = richiesta.get("giorni")
        if not giorni or giorni <= 0:
            return False, "numero di giornate non valido"

    if categoria == "chilometrico":
        km = richiesta.get("km")
        if not km or km <= 0:
            return False, "numero di chilometri non valido"

    if categoria == "alloggio":
        notti = richiesta.get("notti")
        if not notti or notti <= 0:
            return False, "numero di notti non valido"

    # Controllo incompatibilità lavoro agile / trasferta (Sez. 5, solo dal 01/01/2026)
    if richieste_esistenti is not None and data >= rules.DATA_DECORRENZA_2026:
        dipendente = richiesta.get("dipendente")
        date_richiesta = storage.date_coperte(richiesta)
        if date_richiesta:
            if categoria == "lavoro_agile":
                if date_richiesta & storage.date_trasferta_valide(richieste_esistenti, dipendente):
                    return False, "incompatibilità lavoro agile / trasferta"
            elif categoria in ("trasferta_italia", "trasferta_estero"):
                date_agile = set()
                for r in richieste_esistenti:
                    if (
                        r["dipendente"] == dipendente
                        and r["stato"] == "valida"
                        and r["categoria"] == "lavoro_agile"
                    ):
                        date_agile |= storage.date_coperte(r)
                if date_richiesta & date_agile:
                    return False, "incompatibilità lavoro agile / trasferta"

    return True, ""
