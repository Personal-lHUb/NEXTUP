import Link from "next/link";

const ROLES = [
  {
    href: "/client" as const,
    title: "Cliente",
    desc: "Hobbisti che commissionano un oggetto: cosplay, giochi da tavolo, modellismo, ricambi.",
    cta: "Apri dashboard Cliente",
  },
  {
    href: "/maker" as const,
    title: "Maker",
    desc: "Proprietari di stampanti 3D che ricevono lavori compatibili col proprio hardware.",
    cta: "Apri dashboard Maker",
  },
  {
    href: "/designer" as const,
    title: "Progettista",
    desc: "Designer 3D che creano i modelli e li caricano sui server blindati della piattaforma.",
    cta: "Apri dashboard Progettista",
  },
];

const PILLARS = [
  { t: "Escrow", d: "Il cliente paga subito; i fondi restano congelati e vengono sbloccati a Designer e Maker solo a lavoro approvato." },
  { t: "Protezione IP", d: "I file STL/OBJ non sono mai scaricabili. La stampa avviene via streaming G-code temporaneo (OctoPrint/Klipper)." },
  { t: "Logistica integrata", d: "Etichette di spedizione PDF generate dalla piattaforma. Il Maker stampa e spedisce." },
  { t: "Matching per competenza", d: "Abbinamento per skill, recensioni e prezzo — non per vicinanza geografica." },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <div className="flex items-center gap-2">
        <span
          className="grid h-9 w-9 place-items-center rounded-lg font-bold"
          style={{ background: "var(--accent)" }}
        >
          N
        </span>
        <span className="text-xl font-semibold">NextUp</span>
      </div>

      <h1 className="mt-10 max-w-3xl text-4xl font-semibold leading-tight">
        Il marketplace P2P che collega chi immagina, chi progetta e chi stampa.
      </h1>
      <p className="mt-4 max-w-2xl text-lg" style={{ color: "var(--muted)" }}>
        Un oggetto in tre passi: il Cliente descrive l'idea, il Progettista crea il modello 3D,
        il Maker lo materializza. Pagamenti in escrow, file blindati, spedizione inclusa.
      </p>

      <div className="mt-12 grid gap-5 md:grid-cols-3">
        {ROLES.map((r) => (
          <Link
            key={r.href}
            href={r.href}
            className="rounded-xl border p-6 transition-colors hover:border-[var(--accent)]"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <h2 className="text-lg font-semibold">{r.title}</h2>
            <p className="mt-2 text-sm" style={{ color: "var(--muted)" }}>
              {r.desc}
            </p>
            <span className="mt-4 inline-block text-sm font-medium" style={{ color: "var(--accent)" }}>
              {r.cta} →
            </span>
          </Link>
        ))}
      </div>

      <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PILLARS.map((p) => (
          <div
            key={p.t}
            className="rounded-xl border p-5"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <h3 className="text-sm font-semibold" style={{ color: "var(--accent-2)" }}>
              {p.t}
            </h3>
            <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--muted)" }}>
              {p.d}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
