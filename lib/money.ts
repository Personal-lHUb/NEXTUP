import { BASIS_POINTS, SHIPPING_MARGIN_BPS, TAKE_RATE_BPS } from "./constants";

export interface OrderBreakdown {
  designPrice: number;
  printPrice: number;
  itemsTotal: number;
  /** Carrier base cost + platform micro-margin. */
  shippingCost: number;
  shippingCarrierCost: number;
  shippingMargin: number;
  /** Take rate applied to itemsTotal. */
  platformFee: number;
  designerPayout: number;
  makerPayout: number;
  takeRateBps: number;
  /** What the client is charged up front (held in escrow). */
  clientTotal: number;
}

function round2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

/**
 * Computes the full monetary split for an order.
 *
 * The take rate is applied per side so each party keeps (1 - rate) of their own
 * quote. Shipping carries a separate micro-margin and is not subject to the
 * take rate. The client pays itemsTotal + shippingCost into escrow.
 */
export function computeOrderBreakdown(input: {
  designPrice: number;
  printPrice: number;
  shippingCarrierCost: number;
  takeRateBps?: number;
  shippingMarginBps?: number;
}): OrderBreakdown {
  const takeRateBps = input.takeRateBps ?? TAKE_RATE_BPS;
  const shippingMarginBps = input.shippingMarginBps ?? SHIPPING_MARGIN_BPS;

  const designPrice = round2(input.designPrice);
  const printPrice = round2(input.printPrice);
  const itemsTotal = round2(designPrice + printPrice);

  const designerPayout = round2(designPrice * (1 - takeRateBps / BASIS_POINTS));
  const makerPayout = round2(printPrice * (1 - takeRateBps / BASIS_POINTS));
  const platformFee = round2(itemsTotal - designerPayout - makerPayout);

  const shippingCarrierCost = round2(input.shippingCarrierCost);
  const shippingMargin = round2(shippingCarrierCost * (shippingMarginBps / BASIS_POINTS));
  const shippingCost = round2(shippingCarrierCost + shippingMargin);

  const clientTotal = round2(itemsTotal + shippingCost);

  return {
    designPrice,
    printPrice,
    itemsTotal,
    shippingCost,
    shippingCarrierCost,
    shippingMargin,
    platformFee,
    designerPayout,
    makerPayout,
    takeRateBps,
    clientTotal,
  };
}

export function formatEUR(amount: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount);
}
