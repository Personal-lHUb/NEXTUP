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
| Auth + sessione per ruolo (JWT cookie, middleware, guardie) | `lib/auth/*`, `middleware.ts`, `app/api/auth/*` |
| Take rate 12-15% + micro-margine spedizione | `lib/money.ts`, `lib/constants.ts` |
| Escrow (hold → release/refund), Stripe Connect | `lib/services/escrow.ts` |
| Storage reale dei file blindati (S3/R2/MinIO + fallback locale) | `lib/storage/*` |
| Parsing STL (bounding box + volume) | `lib/services/stl.ts` |
| Slicing server-side (CLI PrusaSlicer/Cura + fallback mock) | `lib/services/slicer.ts` |
| Stampa protetta: token G-code monouso a scadenza + OctoPrint | `lib/services/print.ts`, `lib/services/octoprint.ts` |
| Protezione IP (file blindati, mai scaricabili) | `lib/services/file-protection.ts` |
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
  login/ register/         # autenticazione
  client/                  # dashboard cliente (Kanban + dettaglio progetto)
  maker/                   # dashboard maker (stampanti + trova lavori)
  designer/                # dashboard progettista
  api/                     # auth, projects, escrow, qc, matching, shipping,
                           #   printers, designs/upload, print/{start,stream}
middleware.ts              # protezione route per ruolo
components/                # UI condivisa
lib/
  auth/                    # sessione JWT, password, utenti, guardie
  storage/                 # storage S3-compatibile + fallback locale
  money.ts                 # calcolo commissioni/escrow
  services/                # escrow, shipping, matching, file-protection,
                           #   stl, slicer, print, octoprint
  repositories/            # accesso dati (mock o Prisma)
  mock-data.ts             # dati demo per UI senza DB
prisma/
  schema.prisma            # modello dati
  seed.ts                  # dati demo per il DB
```

## Autenticazione (modalità mock)

Account demo — password per tutti: **demo1234**

| Email | Ruoli |
| --- | --- |
| `demo@nextup.dev` | CLIENT + DESIGNER + MAKER |
| `giulia@example.com` | CLIENT |
| `marco@example.com` | DESIGNER |
| `andrea@example.com` | MAKER |

Le route `/client`, `/maker`, `/designer` sono protette dal `middleware.ts`: senza
sessione si viene reindirizzati a `/login`; con un ruolo mancante alla landing.

## Stampa protetta (flusso IP-safe)

1. Il Maker avvia la stampa (`POST /api/print/start`).
2. Il server legge il sorgente blindato (mai esposto), esegue lo **slicing**
   server-side e salva il G-code sotto una chiave **effimera**.
3. Viene restituito un **token monouso a scadenza** (non il file).
4. L'agent della stampante scambia il token una sola volta su
   `GET /api/print/stream`: riceve i byte, l'oggetto effimero viene cancellato e
   il token invalidato (richieste successive → `410 Gone`).

## API principali

| Metodo | Endpoint | Descrizione |
| --- | --- | --- |
| `POST` | `/api/auth/login` `/register` `/logout` · `GET /api/auth/me` | Sessione |
| `GET/POST` | `/api/projects` | Lista / crea progetto (+ ordine + hold escrow) |
| `POST` | `/api/escrow` | `release` ai payee / `refund` al cliente |
| `POST/GET` | `/api/qc` | Decisione QC / sweep silenzio-assenso |
| `GET` | `/api/matching?printerId=…` | Lavori compatibili con una stampante |
| `GET/POST` | `/api/printers` | Lista / aggiungi stampante (Maker) |
| `POST` | `/api/designs/upload` | Upload sorgente blindato (Designer) → metadati |
| `POST` | `/api/print/start` | Avvia stampa protetta → token stream monouso |
| `GET` | `/api/print/stream?token=…` | Scambio monouso del G-code |
| `POST` | `/api/shipping` | Quotazione o generazione etichetta |

## Prossimi passi suggeriti

1. Integrazione Stripe Connect reale (onboarding payee, webhook).
2. Aggregatore corrieri reale (EasyPost/Shippo) per le etichette.
3. Parser OBJ/3MF/STEP (oltre allo STL) per i metadati.
4. Chat per fase (Modellazione / Stampa) e sistema recensioni.
5. Hardening auth: rotazione/revoca sessioni, rate-limit login, refresh token.
