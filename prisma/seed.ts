import { PrismaClient } from "@prisma/client";
import { createHash } from "node:crypto";
import { computeOrderBreakdown } from "../lib/money";

const prisma = new PrismaClient();

// Demo password hash placeholder (replace with a real bcrypt/argon2 hash).
const PW = createHash("sha256").update("demo-password").digest("hex");

async function main() {
  console.log("Seeding NextUp…");

  // ─── Users ───
  const giulia = await prisma.user.upsert({
    where: { email: "giulia@example.com" },
    update: {},
    create: { email: "giulia@example.com", name: "Giulia R.", passwordHash: PW, roles: ["CLIENT"], country: "IT" },
  });
  const luca = await prisma.user.upsert({
    where: { email: "luca@example.com" },
    update: {},
    create: { email: "luca@example.com", name: "Luca B.", passwordHash: PW, roles: ["CLIENT"], country: "IT" },
  });

  const marco = await prisma.user.upsert({
    where: { email: "marco@example.com" },
    update: {},
    create: {
      email: "marco@example.com",
      name: "Marco — DesignLab",
      passwordHash: PW,
      roles: ["DESIGNER"],
      country: "IT",
      stripeAccountId: "acct_demo_designer",
      ratingAvg: 4.8,
      ratingCount: 37,
    },
  });
  const sara = await prisma.user.upsert({
    where: { email: "sara@example.com" },
    update: {},
    create: {
      email: "sara@example.com",
      name: "Sara — MeepleWorks",
      passwordHash: PW,
      roles: ["DESIGNER"],
      country: "IT",
      stripeAccountId: "acct_demo_designer2",
      ratingAvg: 4.9,
      ratingCount: 52,
    },
  });

  const andrea = await prisma.user.upsert({
    where: { email: "andrea@example.com" },
    update: {},
    create: {
      email: "andrea@example.com",
      name: "Andrea",
      passwordHash: PW,
      roles: ["MAKER"],
      country: "IT",
      stripeAccountId: "acct_demo_maker",
      ratingAvg: 4.7,
      ratingCount: 88,
    },
  });
  const elena = await prisma.user.upsert({
    where: { email: "elena@example.com" },
    update: {},
    create: {
      email: "elena@example.com",
      name: "Elena",
      passwordHash: PW,
      roles: ["MAKER"],
      country: "IT",
      stripeAccountId: "acct_demo_maker2",
      ratingAvg: 4.6,
      ratingCount: 41,
    },
  });

  // ─── Printers ───
  await prisma.printer.create({
    data: {
      makerId: andrea.id,
      name: "Prusa MK4",
      technology: "FDM",
      buildX: 250,
      buildY: 210,
      buildZ: 220,
      materials: ["PLA", "PETG", "ABS", "TPU"],
      octoprintUrl: "http://octopi.local",
      octoprintApiKey: "demo-key",
    },
  });
  await prisma.printer.create({
    data: {
      makerId: elena.id,
      name: "Bambu Lab X1 Carbon",
      technology: "FDM",
      buildX: 256,
      buildY: 256,
      buildZ: 256,
      materials: ["PLA", "PETG", "ABS", "NYLON", "TPU"],
    },
  });
  await prisma.printer.create({
    data: {
      makerId: elena.id,
      name: "Elegoo Saturn 3",
      technology: "SLA",
      buildX: 219,
      buildY: 123,
      buildZ: 250,
      materials: ["RESIN_STANDARD", "RESIN_TOUGH", "RESIN_FLEXIBLE"],
      status: "BUSY",
    },
  });

  // ─── Projects (+ order + design file) ───
  await createProject({
    clientId: giulia.id,
    designerId: marco.id,
    makerId: andrea.id,
    title: "Vaso geometrico da esterno",
    description: "Vaso decorativo stampato in PETG, finitura opaca.",
    category: "spare-parts",
    status: "COMPLETED",
    designPrice: 10,
    printPrice: 22,
    material: "PETG",
    bbox: [150, 150, 180],
  });

  await createProject({
    clientId: luca.id,
    designerId: sara.id,
    makerId: andrea.id,
    title: "Organizer per Gloomhaven",
    description: "Set di inserti per scatola gioco da tavolo.",
    category: "boardgames",
    status: "PRINTING",
    designPrice: 35,
    printPrice: 60,
    material: "PETG",
    bbox: [180, 180, 60],
  });

  await createProject({
    clientId: giulia.id,
    designerId: marco.id,
    title: "Casco Mandaloriano (cosplay)",
    description: "Casco indossabile, da stampare in più parti.",
    category: "cosplay",
    status: "MODEL_REVIEW",
    designPrice: 80,
    printPrice: 140,
    material: "PLA",
    bbox: [240, 210, 290],
  });

  await createProject({
    clientId: luca.id,
    designerId: sara.id,
    title: "Miniatura Drago 75mm (resina)",
    description: "Miniatura ad alto dettaglio per modellismo.",
    category: "scale-models",
    status: "MATCHING",
    designPrice: 15,
    printPrice: 30,
    material: "RESIN_STANDARD",
    bbox: [70, 55, 90],
  });

  console.log("Seed complete.");
}

async function createProject(opts: {
  clientId: string;
  designerId: string;
  makerId?: string;
  title: string;
  description: string;
  category: string;
  status: any;
  designPrice: number;
  printPrice: number;
  material: any;
  bbox: [number, number, number];
}) {
  const [x, y, z] = opts.bbox;
  const project = await prisma.project.create({
    data: {
      title: opts.title,
      description: opts.description,
      category: opts.category,
      status: opts.status,
      clientId: opts.clientId,
      designerId: opts.designerId,
      makerId: opts.makerId,
      designPrice: opts.designPrice,
      printPrice: opts.printPrice,
      material: opts.material,
      requiredX: x,
      requiredY: y,
      requiredZ: z,
    },
  });

  await prisma.designFile.create({
    data: {
      designerId: opts.designerId,
      projectId: project.id,
      filename: `${opts.title}.stl`,
      format: "STL",
      storageKey: `protected/${createHash("sha256").update(project.id).digest("hex")}`,
      fileHash: createHash("sha256").update(project.title).digest("hex"),
      sizeBytes: 1_500_000,
      boundingBoxX: x,
      boundingBoxY: y,
      boundingBoxZ: z,
      volumeCm3: Math.round(((x * y * z) / 1000) * 0.12 * 10) / 10,
    },
  });

  const breakdown = computeOrderBreakdown({
    designPrice: opts.designPrice,
    printPrice: opts.printPrice,
    shippingCarrierCost: 7.5,
  });

  await prisma.order.create({
    data: {
      projectId: project.id,
      itemsTotal: breakdown.itemsTotal,
      shippingCost: breakdown.shippingCost,
      platformFee: breakdown.platformFee,
      designerPayout: breakdown.designerPayout,
      makerPayout: breakdown.makerPayout,
      takeRateBps: breakdown.takeRateBps,
      paymentStatus: opts.status === "COMPLETED" ? "RELEASED" : "HELD",
    },
  });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
