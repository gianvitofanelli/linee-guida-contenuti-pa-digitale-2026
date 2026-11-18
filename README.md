# Linee guida di content design – PA digitale 2026

Le regole per scrivere i contenuti di PA digitale 2026: sito pubblico, area riservata, comunicazioni agli enti, assistente virtuale e allegati degli avvisi. Versione 1.2 (bozza).

Il testo sta nei file di `content/`, un file per capitolo. Il sito si genera da lì: la revisione si fa su GitHub, con pull request e issue.

## Come è organizzato

| Cosa | Dove |
| --- | --- |
| Testo dei capitoli (HTML) | `content/NN-nome.html` |
| Ordine, titoli e gruppi dei capitoli | `chapters.json` |
| Nome del sito, versione, indirizzo del repository | `site.json` |
| Aspetto e comportamento del sito | `assets/style.css`, `assets/site.js` |
| Generatore del sito | `build.py` |
| Pubblicazione su GitHub Pages | `.github/workflows/pages.yml` |

## Rivedere e modificare

- **Modificare un capitolo:** apri il file in `content/`, scegli Edit, cambia il testo e apri una pull request. Chi approva usa la revisione della pull request.
- **Proporre una modifica senza scrivere il testo:** apri una issue con il modulo "Proposta di modifica".
- **Nuova versione:** aggiorna `site.json` e `CHANGELOG.md` (numero, data, elenco delle modifiche).

Le regole di scrittura per i capitoli sono quelle del capitolo 0 e del capitolo 11 (governance).

## Generare il sito in locale

Serve solo Python 3, senza librerie esterne.

```
python build.py
```

Il sito compare nella cartella `_site/`. Per vederlo con la ricerca funzionante, avvia un server locale:

```
python -m http.server --directory _site 8000
```

e apri `http://localhost:8000`.

## Pubblicare su GitHub Pages

1. Nelle impostazioni del repository, alla voce Pages, scegli come sorgente GitHub Actions.
2. A ogni push sul ramo `main` il workflow genera il sito e lo pubblica.
3. Per attivare i link "Modifica questo capitolo su GitHub" e "Proponi una modifica", scrivi l'indirizzo del repository in `site.json`, nel campo `repo` (per esempio `https://github.com/organizzazione/nome-repository`).

## Cosa contiene il testo

Capitoli 0 a 11, appendici A e B e il pacchetto per Figma. I testi di esempio, i nomi di enti, persone, CUP e numeri di protocollo sono fittizi.
