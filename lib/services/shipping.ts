import { SHIPPING_MARGIN_BPS, BASIS_POINTS } from "../constants";

/**
 * Shipping abstraction. The platform owns logistics end-to-end: it quotes a
 * carrier rate, applies a micro-margin, and generates a ready-to-print PDF
 * label (carrier networks / lockers / pickup points). The maker only prints
 * the label and ships.
 *
 * With no SHIPPING_API_KEY configured a deterministic mock label is returned.
 */

export interface Address {
  name: string;
  line1: string;
  city: string;
  postalCode: string;
  country: string; // ISO-3166 alpha-2
}

export interface ParcelDimensions {
  weightG: number;
  lengthMm: number;
  widthMm: number;
  heightMm: number;
}

export interface ShippingQuote {
  carrier: string;
  service: string;
  carrierCost: number; // base carrier price
  margin: number; // platform micro-margin
  total: number; // carrierCost + margin (what the client pays)
  currency: string;
}

export interface ShippingLabelResult {
  carrier: string;
  service: string;
  trackingNumber: string;
  labelPdfUrl: string;
  cost: number;
}

export interface ShippingProvider {
  quote(from: Address, to: Address, parcel: ParcelDimensions): Promise<ShippingQuote>;
  createLabel(
    from: Address,
    to: Address,
    parcel: ParcelDimensions,
  ): Promise<ShippingLabelResult>;
}

function withMargin(carrierCost: number): { margin: number; total: number } {
  const margin = Math.round(carrierCost * (SHIPPING_MARGIN_BPS / BASIS_POINTS) * 100) / 100;
  return { margin, total: Math.round((carrierCost + margin) * 100) / 100 };
}

class MockShippingProvider implements ShippingProvider {
  private estimateCarrierCost(from: Address, to: Address, parcel: ParcelDimensions): number {
    const intl = from.country !== to.country;
    const base = intl ? 14.9 : 6.9;
    const perKg = (parcel.weightG / 1000) * (intl ? 4.5 : 2.0);
    return Math.round((base + perKg) * 100) / 100;
  }

  async quote(from: Address, to: Address, parcel: ParcelDimensions): Promise<ShippingQuote> {
    const carrierCost = this.estimateCarrierCost(from, to, parcel);
    const { margin, total } = withMargin(carrierCost);
    return {
      carrier: "NextUp Logistics (mock)",
      service: from.country === to.country ? "Standard Domestic" : "Standard International",
      carrierCost,
      margin,
      total,
      currency: "EUR",
    };
  }

  async createLabel(
    from: Address,
    to: Address,
    parcel: ParcelDimensions,
  ): Promise<ShippingLabelResult> {
    const q = await this.quote(from, to, parcel);
    const tracking = `NU${Date.now().toString(36).toUpperCase()}`;
    return {
      carrier: q.carrier,
      service: q.service,
      trackingNumber: tracking,
      labelPdfUrl: `/api/shipping/label/${tracking}.pdf`, // mock URL; real impl returns a signed PDF
      cost: q.total,
    };
  }
}

// A real provider (EasyPost/Shippo/etc.) would implement the same interface.
let cached: ShippingProvider | null = null;

export function getShippingProvider(): ShippingProvider {
  if (cached) return cached;
  // TODO: when SHIPPING_API_KEY is set, return a real aggregator-backed provider.
  cached = new MockShippingProvider();
  return cached;
}
