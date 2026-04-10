# 📥 Scarica Substack — Downloader di Newsletter

Script Python per scaricare tutti i post pubblici di una newsletter Substack come **PDF** e **Markdown**.

---

## 🎯 Perché questo script

Questo script nasce per studiare il lavoro di un noto giornalista e autore di una delle newsletter più interessanti sulla creator economy italiana.

L'obiettivo non è copiare, ma capire. Come dice lui stesso:

> *"Non si tratta di copiare il lavoro altrui quanto di applicare il concetto dell'ingegneria inversa: smontare un'idea geniale nelle sue parti più piccole, capirne il funzionamento, e ricostruire qualcosa di originale ed efficace per i nostri scopi."*

---

## 🎙️ L'ispirazione

Questo progetto nasce anche grazie al podcast italiano **Prima o Poi**, in cui i conduttori citano strumenti e concetti concreti da mettere in pratica. Ascoltare non basta — bisogna fare. Ed eccoci qui.

La prima repo dopo tanto tempo — creata grazie ad **Ale** — per versionare uno script che forse potrà essere d'aiuto anche ad altri... o anche solo a me. 🙂

---

## ⚙️ Cosa fa

- Recupera tutti i post pubblici tramite le API Substack
- Filtra per range di date
- Salva ogni post come **PDF** (A4, pronto per la stampa)
- Salva ogni post come **Markdown** (base di conoscenza testuale)
- Genera un **indice** con tutti i post linkati

---

## 🚀 Installazione

```bash
pip3 install requests playwright beautifulsoup4 markdownify
python3 -m playwright install chromium
```

## ▶️ Uso

```bash
python3 scarica_scrollinginfinito.py
```

---

## 📁 Output

| Cartella | Contenuto |
|----------|-----------|
| `scrollinginfinito_pdf/` | Un PDF per ogni post |
| `scrollinginfinito_md/` | Un file Markdown per ogni post |
| `scrollinginfinito_md/00_INDICE.md` | Indice completo di tutti i post |

---

*Fatto con curiosità, un podcast e tanta voglia di imparare.*
