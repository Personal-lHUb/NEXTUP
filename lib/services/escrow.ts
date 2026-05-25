import type { OrderBreakdown } from "../money";

/**
 * Escrow abstraction. The client is charged up front; funds are held by the
 * platform and only released to the designer and maker once the work is
 * delivered and approved. Two implementations are provided:
 *
 *  - MockEscrowProvider     — in-memory, for local development / tests.
 *  - StripeConnectEscrow    — Stripe Connect with manual (delayed) payouts.
 *
 * `getEscrowProvider()` returns Stripe when STRIPE_SECRET_KEY is configured,
 * otherwise the mock.
 */

export interface EscrowParticipants {
  /** Stripe Connect account ids for payouts. */
  designerAccountId: string | null;
  makerAccountId: string | null;
}

export interface HoldResult {
  paymentIntentId: string;
  status: "HELD";
}

export interface ReleaseResult {
  designerTransferId: string | null;
  makerTransferId: string | null;
  status: "RELEASED";
}

export interface EscrowProvider {
  /** Charge the client and hold the full amount in escrow. */
  hold(orderId: string, breakdown: OrderBreakdown, currency: string): Promise<HoldResult>;
  /** Release the designer and maker payouts; platform keeps the fee. */
  release(
    orderId: string,
    breakdown: OrderBreakdown,
    participants: EscrowParticipants,
    currency: string,
  ): Promise<ReleaseResult>;
  /** Refund the client (e.g. cancelled / disputed before release). */
  refund(orderId: string, paymentIntentId: string): Promise<{ status: "REFUNDED" }>;
}

// ─────────────────────────── Mock ───────────────────────────

class MockEscrowProvider implements EscrowProvider {
  async hold(orderId: string): Promise<HoldResult> {
    return { paymentIntentId: `mock_pi_${orderId}`, status: "HELD" };
  }

  async release(orderId: string): Promise<ReleaseResult> {
    return {
      designerTransferId: `mock_tr_d_${orderId}`,
      makerTransferId: `mock_tr_m_${orderId}`,
      status: "RELEASED",
    };
  }

  async refund(): Promise<{ status: "REFUNDED" }> {
    return { status: "REFUNDED" };
  }
}

// ─────────────────────── Stripe Connect ──────────────────────
// Real implementation. Charges go to the platform account and are held;
// payouts are issued as separate transfers to connected accounts on release,
// so funds genuinely sit in escrow until QC approval.

class StripeConnectEscrow implements EscrowProvider {
  constructor(private readonly secretKey: string) {}

  // Lazy-load the SDK so the mock path has no hard dependency on `stripe`.
  private async client() {
    const Stripe = (await import("stripe")).default;
    return new Stripe(this.secretKey);
  }

  private toCents(amount: number): number {
    return Math.round(amount * 100);
  }

  async hold(orderId: string, breakdown: OrderBreakdown, currency: string): Promise<HoldResult> {
    const stripe = await this.client();
    const pi = await stripe.paymentIntents.create({
      amount: this.toCents(breakdown.clientTotal),
      currency: currency.toLowerCase(),
      capture_method: "automatic",
      metadata: { orderId, kind: "escrow_hold" },
    });
    return { paymentIntentId: pi.id, status: "HELD" };
  }

  async release(
    orderId: string,
    breakdown: OrderBreakdown,
    participants: EscrowParticipants,
    currency: string,
  ): Promise<ReleaseResult> {
    const stripe = await this.client();
    const cur = currency.toLowerCase();

    let designerTransferId: string | null = null;
    if (participants.designerAccountId && breakdown.designerPayout > 0) {
      const t = await stripe.transfers.create({
        amount: this.toCents(breakdown.designerPayout),
        currency: cur,
        destination: participants.designerAccountId,
        metadata: { orderId, role: "DESIGNER" },
      });
      designerTransferId = t.id;
    }

    let makerTransferId: string | null = null;
    if (participants.makerAccountId && breakdown.makerPayout > 0) {
      const t = await stripe.transfers.create({
        amount: this.toCents(breakdown.makerPayout),
        currency: cur,
        destination: participants.makerAccountId,
        metadata: { orderId, role: "MAKER" },
      });
      makerTransferId = t.id;
    }

    return { designerTransferId, makerTransferId, status: "RELEASED" };
  }

  async refund(orderId: string, paymentIntentId: string): Promise<{ status: "REFUNDED" }> {
    const stripe = await this.client();
    await stripe.refunds.create({ payment_intent: paymentIntentId });
    return { status: "REFUNDED" };
  }
}

// ─────────────────────────── Factory ─────────────────────────

let cached: EscrowProvider | null = null;

export function getEscrowProvider(): EscrowProvider {
  if (cached) return cached;
  const key = process.env.STRIPE_SECRET_KEY;
  cached = key ? new StripeConnectEscrow(key) : new MockEscrowProvider();
  return cached;
}
