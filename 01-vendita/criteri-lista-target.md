# Criteri Lista Target — 100 aziende in ~3 ore

> Documento interno. Obiettivo: lista di 100 aziende qualificate (serramentisti, fotovoltaico, HVAC) su Bologna, Modena, Reggio Emilia, Parma. Tempo stimato: 3 ore in 2 sessioni da 90 minuti.

## Regola d'oro (prima di tutto)

Il Sistema Risposta Rapida Lead **non genera richieste: risponde a quelle che già arrivano**. Quindi cerchiamo solo aziende che hanno **già** un form sul sito e fanno **già** pubblicità su Google. Se non hanno lead in entrata, non sono un target. Punto.

## Passo 1 — Ricerca su Google Maps (60–75 min)

Apri Google Maps, cerca città per città. Per ogni risultato con sito web, apri il sito in una nuova scheda.

### Query esatte da usare

**Serramentisti** (ripeti per: Bologna, Modena, Reggio Emilia, Parma)
- `serramenti [CITTÀ]`
- `infissi [CITTÀ]`
- `finestre pvc [CITTÀ]`
- `porte e finestre [CITTÀ]`

**Fotovoltaico** (ripeti per le 4 città)
- `impianti fotovoltaici [CITTÀ]`
- `installazione fotovoltaico [CITTÀ]`
- `fotovoltaico aziende [CITTÀ]`
- `pannelli solari installazione [CITTÀ]`

**HVAC / clima e caldaie** (ripeti per le 4 città)
- `installazione caldaie [CITTÀ]`
- `climatizzatori installazione [CITTÀ]`
- `condizionatori assistenza [CITTÀ]`
- `impianti termoidraulici [CITTÀ]`

Obiettivo grezzo: ~150–180 nomi da scremare fino a 100. Ripartizione indicativa: 35 serramentisti, 35 fotovoltaico, 30 HVAC.

## Passo 2 — Qualifica (60 min, ~30 secondi ad azienda)

Un'azienda entra in lista **solo se passa tutti e 4 i controlli**:

1. **Form funzionante sul sito.** Cerca la pagina "Contatti" o "Richiedi preventivo". Deve esserci un form vero (nome, telefono/email, messaggio). Se c'è solo numero di telefono o indirizzo email scritto in pagina → fuori.
2. **Google Ads attive.** Apri una finestra in incognito, cerca su Google `[NOME AZIENDA] [CITTÀ]` e poi 1–2 query di mestiere (es. `serramenti [CITTÀ]`). Se compare tra gli annunci "Sponsorizzato" in alto → spende in pubblicità → ha lead in entrata → target perfetto. Segna Sì/No nel CSV.
3. **3–15 dipendenti stimati.** Stima da: pagina "Chi siamo" (foto squadra), numero di mezzi/furgoni nelle foto, pagina LinkedIn aziendale, recensioni che citano i montatori. Sotto 3 = il titolare fa tutto e non paga; sopra 15 = probabilmente hanno già struttura interna.
4. **Sito curato, non abbandonato.** Indizi buoni: foto reali dei lavori, ultima notizia/post recente, certificazioni esposte, partita IVA nel footer. Indizi cattivi: "Sito in costruzione", copyright fermo a 3+ anni fa, foto stock ovunque, testo segnaposto.

### Squalifica immediata (non perderci tempo)

- Nessun form: solo telefono e indirizzo → fuori.
- Sito morto, in costruzione o irraggiungibile → fuori.
- Solo pagina Facebook senza sito → fuori.
- Grande azienda/franchising nazionale (call center, sedi multiple in tutta Italia) → fuori.
- Rivenditore puro senza installazione → fuori (il sopralluogo lo fa qualcun altro).

> Nota: la presenza Google Ads è il segnale più forte ma non eliminatorio da sola. Form OK + sito curato + niente Ads = tienila in lista come priorità B. Niente form = fuori sempre.

## Passo 3 — Trovare nome ed email del titolare (45–60 min)

In ordine di velocità:

1. **Pagina "Chi siamo" / "La nostra storia"** del sito: spesso c'è "fondata da [NOME]" o la foto del titolare con nome.
2. **Hunter.io** (50 ricerche gratis/mese): inserisci il dominio, ti restituisce le email trovate e il formato tipico (es. `nome@azienda.it` vs `info@azienda.it`). Usa le 50 ricerche solo sulle aziende migliori, non sprecarle.
3. **LinkedIn**: cerca `[NOME AZIENDA]` e guarda chi si presenta come Titolare / Fondatore / Amministratore. Spesso da lì ricavi nome e cognome, poi costruisci l'email col formato visto su Hunter.
4. **Visura veloce gratis**: cerca `[NOME AZIENDA] + P.IVA` — su registri online pubblici spesso compare il nome dell'amministratore.
5. **Fallback**: se non trovi l'email personale, usa `info@` ma scrivi nell'oggetto "alla cortese attenzione del titolare" e cita il suo nome se lo conosci.

## Passo 4 — Compila il CSV

Ogni azienda qualificata va in `lista-target.csv` con tutti i campi compilati. Stato iniziale: `Da contattare`. Le aziende con Google Ads attive vanno contattate per prime.

## Checklist finale

- [ ] 100 aziende in lista (minimo 80 per partire)
- [ ] Tutte con form verificato funzionante
- [ ] Colonna Google Ads compilata (Sì/No) per tutte
- [ ] Almeno 60% con nome del titolare trovato
- [ ] Almeno 50% con email diretta (non solo info@)
- [ ] Nessun cliente/fornitore/concorrente del mio datore di lavoro in lista
