# Metodo di lavoro

Come si passa da "voglio vendere libri su KDP" a un catalogo che regge nel tempo.
La pipeline copre la produzione; questo documento copre le decisioni che la
precedono e la seguono.

---

## 1. Scegliere l'argomento prima dello strumento

Il fattore che decide se un libro vende non è la qualità della generazione: è
l'incrocio fra un problema che qualcuno cerca su Amazon e un taglio che nessuno
ha ancora dato.

Un metodo rapido, mezz'ora per idea:

1. Cerca su Amazon.it il tema in forma di problema ("gestione del tempo",
   "ansia da esame", "orto sul balcone"). Guarda i **suggerimenti automatici**
   della barra di ricerca: sono query reali.
2. Apri i primi 10 risultati. Annota: prezzo, numero di pagine, data di
   pubblicazione, numero di recensioni.
3. Leggi le **recensioni a 2 e 3 stelle** dei più venduti. È lì che i lettori
   scrivono cosa manca: "troppo generico", "nessun esempio pratico", "parla solo
   di aziende americane". Ognuna di quelle frasi è il taglio del tuo libro.
4. Scarta la nicchia se: i primi risultati hanno migliaia di recensioni e sono
   di editori grossi; oppure se non trovi nemmeno dieci libri (di solito vuol
   dire che nessuno cerca quel tema).

Riporta quello che hai trovato nei campi `topic`, `audience`, `promise` e
soprattutto `notes` di `book.json`: è il materiale che rende il libro diverso
dagli altri.

## 2. Scegliere la lunghezza

| Pagine | Formato tipico | Quando ha senso |
|---|---|---|
| 60-90 | 5x8 o 5.5x8.5 | guida operativa su un problema singolo, prezzo basso, lettura in un'ora |
| 100-150 | 6x9 | il formato standard della non-fiction pratica: un metodo completo |
| 160-240 | 6x9 | trattazione ampia, più adatta a chi ha già un pubblico |

Sotto le 79 pagine non puoi mettere il testo sul dorso: in libreria online conta
poco, ma un libro sottile comunica meno valore percepito. Sopra le 240 pagine il
costo di stampa erode la royalty e il rischio di parti deboli cresce.

## 3. Produzione

```bash
python3 -m kdpfactory init "Titolo di lavoro" --pages 140 --topic "..." --audience "..."
$EDITOR books/<slug>/book.json          # il passaggio che conta
python3 -m kdpfactory outline <slug>
$EDITOR books/<slug>/outline.json       # correggi i titoli deboli PRIMA di scrivere
python3 -m kdpfactory write <slug>
python3 -m kdpfactory build <slug>
python3 -m kdpfactory review <slug>      # il collegio legge e segnala
python3 -m kdpfactory revise <slug>      # l'editor applica
python3 -m kdpfactory build <slug>       # si rimpagina: l'editing cambia le pagine
python3 -m kdpfactory metadata <slug>
python3 -m kdpfactory qa <slug>
```

`kdpfactory all <slug>` esegue questa sequenza da sola, al livello di
lavorazione scelto con `--qualita` (vedi [`agenti.md`](agenti.md)).

Due punti in cui intervenire a mano rende molto:

- **Dopo `outline`**: i titoli di capitolo generici ("Le basi del metodo") sono
  il primo segnale di un libro generico. Riscrivili e correggi i `beats`:
  i capitoli verranno scritti su quelli.
- **Dopo `write`**: leggi il primo capitolo per intero. Se il tono non va, non
  proseguire — aggiusta `tone` e `notes`, poi rilancia
  `write <slug> --only 1 --overwrite` finché il capitolo non ti convince. Tutti
  gli altri capitoli erediteranno quelle istruzioni.

Per rigenerare un singolo capitolo: `write <slug> --only 5 --overwrite`.
Per rimettere in riga solo le pagine: `build <slug>`.

## 4. Revisione umana (non saltabile)

Il collegio di agenti toglie di mezzo il lavoro meccanico — dati non
verificabili, ripetizioni, capitoli che non mantengono la promessa, difetti di
impaginazione — ma non sostituisce la lettura. Parti da `build/revisioni.md`:
dice già dove guardare.

- Leggi il manoscritto unico (`build/<slug>-manoscritto.md`), non i file sparsi.
- Segna ogni affermazione che non sapresti difendere davanti a un lettore
  esperto. Riscrivila o toglila.
- Verifica che gli esempi non si assomiglino tutti: è il difetto più frequente
  dei testi generati. Se due capitoli usano la stessa situazione, cambiane una.
- Leggi ad alta voce l'introduzione e le prime due pagine del primo capitolo:
  sono le pagine dell'anteprima "Guarda dentro", quelle che decidono l'acquisto.

## 5. Pubblicazione

Segui [`checklist-kdp.md`](checklist-kdp.md). In sintesi: carica l'interno,
carica la copertina generata **dopo** l'impaginazione finale, compila la scheda
da `build/kdp-listing.md`, dichiara l'uso dell'IA, controlla l'anteprima di
stampa, ordina una copia di prova.

## 6. Dopo la pubblicazione

- **Un titolo alla volta, fino al primo che vende.** Pubblicare dieci libri
  mediocri insieme non produce dieci volte i risultati: produce dieci volte il
  lavoro di manutenzione. Il primo libro serve a capire se la nicchia risponde.
- **Guarda i dati a 30 giorni**: impressioni, clic, conversione. Se il libro
  viene visto e non comprato, il problema è copertina, titolo o descrizione — non
  il contenuto. Si correggono in mezz'ora e si ricaricano.
- **Se un libro vende, scrivi il secondo nella stessa nicchia**, non in una
  nuova. Un lettore soddisfatto è il canale di vendita più economico che hai.
- **Aggiorna i libri che vendono.** Una seconda edizione con i suggerimenti
  raccolti dalle recensioni vale più di un titolo nuovo.

## 7. Cosa non fare

- Pubblicare il risultato del `--dry-run` (è testo segnaposto, il QA lo blocca).
- Pubblicare senza aver letto il libro.
- Produrre varianti quasi identiche dello stesso titolo: Amazon le rimuove.
- Usare nomi di autori noti, marchi o titoli altrui nelle keyword o nel titolo.
- Spostare il problema su più account per superare il limite giornaliero di
  caricamenti: porta alla chiusura dell'account.
