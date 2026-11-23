# Registro delle versioni

## 1.2 (bozza) – 18 novembre 2026

- Sito basato su Bootstrap Italia 2.18.3, copiato in `assets/bootstrap-italia/` (nessuna risorsa esterna: i font Titillium Web e Roboto Mono, le icone e gli script si caricano dal sito stesso). Usa i componenti ufficiali: skiplinks, intestazione con fascia sottile, zona centrale e ricerca in finestra modale, menu dei capitoli a comparsa su mobile, barra laterale, breadcrumb, card, pulsanti, tabelle, footer e pulsante «Torna su». `assets/style.css` contiene solo le estensioni (tabelle Sì/No, schede impilate, impaginazione del testo).
- Logo di PA digitale 2026, preso dal sito padigitale2026.gov.it, nell’intestazione e nel footer (`assets/logo-pa-digitale-2026.svg`).
- Tabelle su schermi stretti (fino a 600 px): le tabelle con tre o più colonne diventano schede impilate, con la semantica di tabella mantenuta tramite ruoli ARIA.
- Sito su mobile: intestazione fissa in alto con pulsanti Cerca e Capitoli, indice dei capitoli a pannello laterale (chiusura con Esc, focus gestito), ricerca comprimibile, tabelle scorrevoli con larghezza minima. Su tutti i dispositivi: pulsante «Torna su» fisso.
- Accessibilità del sito: indicatore di focus ad alto contrasto, gerarchia dei titoli corretta in «Principi» e «Fonti», tabelle scorrevoli raggiungibili da tastiera, ricerca con annuncio dei risultati e frecce direzionali, intestazioni di colonna con `scope`.
- Il testo passa su GitHub: un file per capitolo, revisione con pull request e issue.
- Tolto il capitolo "Decisioni sulle regole". La checklist e la governance diventano il capitolo 11.
- Capitolo 0.4: tra le fonti restano l’analisi del sito padigitale2026.gov.it e il confronto con le migliori pratiche internazionali, senza l’elenco di allegati e guide di stile. Nelle fonti le FAQ non citano più un tema specifico.
- Glossario: “verifiche di conformità tecnica” e “controlli formali” al posto di “Asseverazione tecnica” e “Asseverazione formale”.
- Fonti: il materiale revisionato per il Dipartimento è descritto in modo generico.
- Capitolo 8.5: nella riga "Pulsanti e link" restano solo i testi dei pulsanti.
- La pagina Pacchetto per Figma diventa Intelligenza artificiale: prima i file .md da scaricare e le istruzioni per assistenti come Claude, ChatGPT e Gemini, poi la sezione su Figma.
- I file .md si generano dal testo dei capitoli a ogni pubblicazione.
