# Piano di adeguamento — Circolare MEF n. 18/2026

**Riferimento normativo:** Circolare MEF n. 18/2026 – Codice MEF26-RSD-018 v1.2 del 16/02/2026  
**Decorrenza nuove regole:** 01/01/2026  
**Sostituisce:** Circolare n. 41/2024 (massimali 2025)  
**Regime transitorio:** le spese con data di sostenimento ≤ 31/12/2025 restano calcolate con i massimali e il plafond della Circolare 41/2024, anche se la richiesta è presentata nel 2026.

---

## Differenziale normativo

| Categoria | Fino al 31/12/2025 | Dal 01/01/2026 |
|---|---|---|
| `trasferta_italia` | 46,48 €/giorno | **50,00 €/giorno** |
| `trasferta_estero` | 77,47 €/giorno | **85,00 €/giorno** + progressiva >5 gg |
| `pasto` | 8,00 €/giorno | **10,00 €/giorno** |
| `chilometrico` | 0,42 €/km | **0,45 €/km** |
| `alloggio` | 150,00 €/notte | **170,00 €/notte** |
| `lavoro_agile` | non prevista | **3,50 €/giorno**, max 12 gg/mese |
| Plafond mensile | 1.200,00 €/mese | **1.400,00 €/mese** |

### Progressiva trasferta estero (solo data ≥ 2026-01-01)

Per trasferte all'estero con durata > 5 giornate:

| Giornate | Massimale giornaliero |
|---|---|
| 1ª – 5ª | 85,00 € (pieno) |
| 6ª – 10ª | 76,50 € (−10%) |
| 11ª in poi | 68,00 € (−20%) |

Formula: `massimale = min(G,5)×85 + min(max(G−5,0),5)×76,50 + max(G−10,0)×68`

### Indennità lavoro agile (solo data ≥ 2026-01-01)

- Massimale: 3,50 €/giorno × giornate ammesse nel mese.
- Limite mensile: max 12 giornate per mese di calendario (somma di tutte le richieste valide del dipendente nel mese).
- La quota esente concorre al plafond mensile di 1.400 €.
- **Incompatibilità:** una richiesta di `lavoro_agile` è respinta integralmente se anche una sola giornata ricade nel periodo di una trasferta valida dello stesso dipendente (e viceversa).

---

## Regole transitorie (Sezione 7)

1. Data sostenimento ≤ 31/12/2025 → massimali 41/2024 + plafond 1.200 €.
2. La categoria `lavoro_agile` è respinta ("categoria non riconosciuta") per giornate anteriori al 01/01/2026.
3. La progressiva trasferta estero (Sez. 4) si applica solo per date dal 01/01/2026.
4. Le richieste già liquidate **non** vengono ricalcolate.

---

## Fasi di implementazione

### Fase 1 — `src/rules.py`

**Modifiche:**

- Aggiungere `REGOLE_2025` (dict con parametri 41/2024: massimali, km, notte, plafond=1200, no lavoro_agile).
- Aggiungere `REGOLE_2026` (dict con parametri 18/2026: massimali aggiornati, lavoro_agile=3.50, max_giorni_lavoro_agile=12, plafond=1400).
- Aggiungere funzione `regole_per_data(data_str) -> dict` — ritorna `REGOLE_2026` se `data_str >= "2026-01-01"`, altrimenti `REGOLE_2025`.
- Aggiungere `"lavoro_agile": "Indennità lavoro agile"` in `CATEGORIE`.
- Aggiungere `"lavoro_agile"` in `CATEGORIE_A_GIORNATE`.
- Aggiornare le costanti flat (MASSIMALI_GIORNALIERI, MASSIMALE_KM, MASSIMALE_NOTTE, PLAFOND_MENSILE) ai valori 2026 (usate dal template `/normativa`).
- Aggiornare `RIFERIMENTO_NORMATIVO` a `"Circolare MEF n. 18/2026"`.

---

### Fase 2 — `src/calculator.py`

**Modifiche:**

- In `massimale_teorico(richiesta)`: derivare `regole = rules.regole_per_data(richiesta["data"])` e usare i parametri del dict invece delle costanti flat.
- Aggiungere `_massimale_trasferta_estero_progressiva(giorni, regole) -> float` (formula G1/G2/G3 sopra; attiva solo per regole 2026).
- Aggiungere `_massimale_lavoro_agile(giorni, giornate_gia_usate, regole) -> float`:
  - `ammesse = min(giorni, max(regole["max_giorni_lavoro_agile"] − giornate_gia_usate, 0))`
  - `return round(regole["massimali_giornalieri"]["lavoro_agile"] × ammesse, 2)`
- Aggiornare `calcola(richiesta, esente_gia_riconosciuta, giornate_agile_nel_mese=0)`:
  - Usare `regole["plafond_mensile"]` al posto di `rules.PLAFOND_MENSILE` fisso.
  - Aggiungere `"giornate_ammesse_agile"` nel dettaglio (solo per `lavoro_agile`).

---

### Fase 3 — `src/storage.py`

**Nuove funzioni (nessuna modifica alle esistenti):**

- `giornate_lavoro_agile_nel_mese(richieste, dipendente, mese_riferimento) -> int`
  - Somma `r["giorni"]` delle richieste valide di `lavoro_agile` del dipendente nel mese.
- `date_coperte(richiesta) -> set[str]`
  - Per richieste con campo `giorni`: genera il set di date ISO `[data_inizio, ..., data_inizio + giorni − 1]`.
- `date_trasferta_valide(richieste, dipendente) -> set[str]`
  - Unione delle `date_coperte` di tutte le richieste valide di `trasferta_italia` / `trasferta_estero` del dipendente.

---

### Fase 4 — `src/validator.py`

**Modifiche:**

- Nuova firma: `valida(richiesta, richieste_esistenti=None)` (parametro opzionale → non rompe i test esistenti).
- Aggiungere check: `lavoro_agile` con `data < "2026-01-01"` → `False, "categoria non riconosciuta"`.
- Aggiungere check incompatibilità (solo se `richieste_esistenti` fornito e `data >= "2026-01-01"`):
  - Se categoria è `lavoro_agile`: intersecare `date_coperte(richiesta)` con `storage.date_trasferta_valide(richieste_esistenti, dipendente)` → se non vuoto → `False, "incompatibilità lavoro agile / trasferta"`.
  - Se categoria è `trasferta_italia` o `trasferta_estero`: controllare date coperte da richieste valide di `lavoro_agile` dello stesso dipendente → se non vuoto → stessa motivazione.

---

### Fase 5 — `src/app.py`

**Modifiche:**

- In `_registra()`:
  - Passare `richieste` a `validator.valida(richiesta, richieste)`.
  - Per richiesta valida con categoria `lavoro_agile`: chiamare `storage.giornate_lavoro_agile_nel_mese()` e passare a `calculator.calcola(..., giornate_agile_nel_mese=n)`.
- In `riepilogo()`:
  - Calcolare `percentuale_plafond` usando `rules.regole_per_data(mese + "-01")["plafond_mensile"]` per riga (mese 2025 → 1200, mese 2026 → 1400).

---

### Fase 6 — Templates e static

**`src/templates/normativa.html`:**
- Aggiungere riga `lavoro_agile` nella tabella (3,50 €/gg, max 12 gg/mese).
- Aggiungere nota sulla progressiva trasferta estero >5 gg.
- Aggiornare il loop massimali per coprire `lavoro_agile`.
- Aggiornare la sezione "Come avviene il calcolo" per citare la progressiva e l'incompatibilità.

**`src/static/app.js`:**
- Verificare che il selettore JS che mostra/nasconde il campo `giorni` copra già `lavoro_agile` (che rientra in `CATEGORIE_A_GIORNATE`) — aggiornare se necessario.

---

### Fase 7 — Tests

#### `tests/test_calculator.py`

I test esistenti usano `data: "2025-10-06"` → continuano a usare i massimali 41/2024, **non si rompono**.

Aggiungere:
- Massimali 2026 aggiornati per ogni categoria (data 2026).
- `test_trasferta_estero_progressiva_6_giorni` → massimale atteso 501,50 € (5×85 + 1×76,50).
- `test_trasferta_estero_progressiva_12_giorni` → massimale atteso 943,50 € (caso PDF).
- `test_trasferta_estero_5_giorni_esatti_no_progressiva` → 425,00 € (5×85).
- `test_lavoro_agile_entro_limite` (6 gg, 0 già usate → 21,00 €).
- `test_lavoro_agile_giornate_eccedenti` (15 gg, 0 usate → max 12 → 42,00 €).
- `test_lavoro_agile_limite_parziale` (6 gg, già 8 usate → ammesse 4 → 14,00 €).
- `test_plafond_2026_1400` (data 2026, `esente_gia=1350`, capienza 50 €).

#### `tests/test_validator.py`

Aggiungere:
- `test_lavoro_agile_valido` (data 2026-03-01, giorni=5).
- `test_lavoro_agile_data_2025_respinto` → "categoria non riconosciuta".
- `test_lavoro_agile_giornate_non_valide`.
- `test_incompatibilita_agile_su_giorno_trasferta`.
- `test_incompatibilita_trasferta_su_giorno_agile`.
- `test_compatibilita_agile_senza_sovrapposizione`.
- `test_no_incompatibilita_se_richiesta_trasferta_e_respinta`.

#### `tests/test_app.py`

I test esistenti con data 2025 restano validi. Aggiungere:
- `test_plafond_2026_1400` (due richieste data 2026, secondo plafond 1400).
- `test_lavoro_agile_registrato_correttamente`.
- `test_lavoro_agile_respinto_per_incompatibilita`.
- `test_trasferta_estera_progressiva`.
- `test_transitorio_richiesta_2025_in_2026_usa_massimali_vecchi`.

---

## File modificati

| File | Tipo modifica |
|---|---|
| `src/rules.py` | Aggiunta REGOLE_2025/2026, regole_per_data(), update CATEGORIE |
| `src/calculator.py` | Transitorio + progressiva + lavoro_agile |
| `src/storage.py` | 3 nuove funzioni (no modifica a quelle esistenti) |
| `src/validator.py` | Firma aggiornata + 2 nuovi check |
| `src/app.py` | _registra() + riepilogo() |
| `src/templates/normativa.html` | Tabella + note |
| `src/static/app.js` | Verifica/aggiornamento visibilità campo giorni |
| `tests/test_calculator.py` | +8 test nuovi |
| `tests/test_validator.py` | +7 test nuovi |
| `tests/test_app.py` | +5 test nuovi |

---

## Checklist verifiche finali

- [ ] `python -m pytest tests/ -v` — tutti i test passano.
- [ ] Trasferta estero 12 gg data 2026 → massimale calcolato 943,50 €.
- [ ] `lavoro_agile` con data 2025 → respinta "categoria non riconosciuta".
- [ ] `lavoro_agile` sovrapposto a trasferta stessa settimana → respinta "incompatibilità lavoro agile / trasferta".
- [ ] `/normativa` mostra massimali 2026, nota progressiva, riga lavoro_agile.
- [ ] `/riepilogo`: mese 2025 usa percentuale su 1.200 €, mese 2026 su 1.400 €.
- [ ] Richieste già liquidate non vengono ricalcolate (storico immutabile).
