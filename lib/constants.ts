// Central tunables. Values fall back to sane defaults when env vars are unset.

export const TAKE_RATE_BPS = Number(process.env.PLATFORM_TAKE_RATE_BPS ?? 1300); // 13%
export const SHIPPING_MARGIN_BPS = Number(process.env.SHIPPING_MARGIN_BPS ?? 500); // 5%
export const QC_AUTO_APPROVE_HOURS = Number(process.env.QC_AUTO_APPROVE_HOURS ?? 48);

export const USE_MOCK_DATA = (process.env.USE_MOCK_DATA ?? "true") === "true";

export const CATEGORIES = [
  { slug: "cosplay", label: "Cosplay" },
  { slug: "boardgames", label: "Giochi da tavolo" },
  { slug: "scale-models", label: "Modellismo" },
  { slug: "spare-parts", label: "Ricambi" },
] as const;

export const BASIS_POINTS = 10_000;
