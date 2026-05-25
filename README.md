# NextUp

Marketplace P2P di stampa 3D che collega tre figure:

- **Cliente** (hobbista: cosplay, giochi da tavolo, modellismo, ricambi)
- **Progettista** (designer 3D che crea i modelli digitali)
- **Maker** (proprietario di stampante 3D che materializza l'oggetto)

Questo repository è lo **scaffold full-stack fondativo**: struttura, modello dati,
dashboard e flussi principali sono in piedi; le integrazioni esterne (Stripe,
corrieri, object storage, slicing/streaming) sono astratte dietro interfacce con
implementazioni mock, pronte per essere collegate ai provider reali.

## Stack

- **Next.js 15** (App Router) + **React 19** + **TypeScript**
- **PostgreSQL** + **Prisma ORM**
- **Tailwind CSS v4**
- **Stripe Connect** per pagamenti/escrow (stub finché non si configurano le chiavi)
- **Zod** per la validazione degli input API

## Avvio rapido

```bash
# 1. Dipendenze
npm install

# 2. Variabili d'ambiente
cp .env.example .env

# 3a. (Opzionale) UI navigabile senza database
#     USE_MOCK_DATA=true (default) → le dashboard usano dati in memoria
npm run dev        # http://localhost:3000

# 3b. Con database reale
docker compose up -d          # Postgres locale
# imposta USE_MOCK_DATA=false in .env
npm run db:generate
npm run db:migrate            # crea le tabelle
npm run db:seed               # dati demo
npm run dev
```

## Concetti chiave implementati

| Requisito | Dove |
| --- | --- |
| Modello dati a 3 lati (utenti, ruoli, progetti, ordini, stampanti, file, spedizioni) | `prisma/schema.prisma` |
| Take rate 12-15% + micro-margine spedizione | `lib/money.ts`, `lib/constants.ts` |
| Escrow (hold → release/refund), Stripe Connect | `lib/services/escrow.ts` |
| Protezione IP (file blindati, G-code temporaneo single-use) | `lib/services/file-protection.ts` |
| Matching per compatibilità hardware (volume + materiali), non geografico | `lib/services/matching.ts` |
| Logistica + etichette PDF | `lib/services/shipping.ts` |
| QC con 3 foto + "silenzio assenso" 48h | `app/api/qc/route.ts`, `components/QCApproval.tsx` |
| Dashboard Cliente (Kanban, viewer watermark, approvazione foto) | `app/client/*`, `components/KanbanBoard.tsx`, `ModelViewer.tsx` |
| Dashboard Maker (stampanti, trova lavori, stampa protetta) | `app/maker/page.tsx`, `components/JobBoard.tsx` |
| Dashboard Progettista (upload protetto, commesse) | `app/designer/page.tsx` |

## Struttura

```
app/
  page.tsx                 # landing
  client/                  # dashboard cliente (Kanban + dettaglio progetto)
  maker/                   # dashboard maker (stampanti + trova lavori)
  designer/                # dashboard progettista
  api/                     # projects, escrow, qc, matching, shipping, printers
components/                # UI condivisa
lib/
  money.ts                 # calcolo commissioni/escrow
  services/                # escrow, shipping, matching, file-protection
  repositories/            # accesso dati (mock o Prisma)
  mock-data.ts             # dati demo per UI senza DB
prisma/
  schema.prisma            # modello dati
  seed.ts                  # dati demo per il DB
```

## API principali

| Metodo | Endpoint | Descrizione |
| --- | --- | --- |
| `GET/POST` | `/api/projects` | Lista / crea progetto (+ ordine + hold escrow) |
| `POST` | `/api/escrow` | `release` ai payee / `refund` al cliente |
| `POST/GET` | `/api/qc` | Decisione QC / sweep silenzio-assenso |
| `GET` | `/api/matching?printerId=…` | Lavori compatibili con una stampante |
| `GET/POST` | `/api/printers` | Stampanti / aggiungi / avvia stampa protetta |
| `POST` | `/api/shipping` | Quotazione o generazione etichetta |

## Prossimi passi suggeriti

1. Autenticazione e sessione ruolo (NextAuth o simile).
2. Object storage reale per i file blindati + slicing server-side → streaming G-code.
3. Integrazione Stripe Connect reale (onboarding payee, webhook).
4. Aggregatore corrieri reale (EasyPost/Shippo) per le etichette.
5. Chat per fase (Modellazione / Stampa) e sistema recensioni.
