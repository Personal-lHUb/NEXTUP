import bcrypt from "bcryptjs";
import { USE_MOCK_DATA } from "../constants";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
  passwordHash: string;
  stripeAccountId?: string;
}

// Demo credentials for USE_MOCK_DATA mode. Password for every account: demo1234
export const DEMO_PASSWORD = "demo1234";

let mockUsers: AuthUser[] | null = null;
function getMockUsers(): AuthUser[] {
  if (mockUsers) return mockUsers;
  const passwordHash = bcrypt.hashSync(DEMO_PASSWORD, 10);
  mockUsers = [
    { id: "usr_demo", email: "demo@nextup.dev", name: "Demo (tutti i ruoli)", roles: ["CLIENT", "DESIGNER", "MAKER"], passwordHash },
    { id: "usr_giulia", email: "giulia@example.com", name: "Giulia R.", roles: ["CLIENT"], passwordHash },
    { id: "usr_marco", email: "marco@example.com", name: "Marco — DesignLab", roles: ["DESIGNER"], passwordHash },
    { id: "usr_andrea", email: "andrea@example.com", name: "Andrea", roles: ["MAKER"], passwordHash },
  ];
  return mockUsers;
}

export async function findUserByEmail(email: string): Promise<AuthUser | null> {
  const normalized = email.trim().toLowerCase();
  if (USE_MOCK_DATA) {
    return getMockUsers().find((u) => u.email === normalized) ?? null;
  }
  const { prisma } = await import("../prisma");
  const u = await prisma.user.findUnique({ where: { email: normalized } });
  if (!u) return null;
  return {
    id: u.id,
    email: u.email,
    name: u.name,
    roles: u.roles,
    passwordHash: u.passwordHash,
    stripeAccountId: u.stripeAccountId ?? undefined,
  };
}

export async function createUser(input: {
  email: string;
  name: string;
  passwordHash: string;
  roles: string[];
}): Promise<AuthUser> {
  const normalized = input.email.trim().toLowerCase();
  if (USE_MOCK_DATA) {
    const users = getMockUsers();
    if (users.some((u) => u.email === normalized)) {
      throw new Error("EMAIL_TAKEN");
    }
    const user: AuthUser = { id: `usr_${Date.now()}`, email: normalized, name: input.name, roles: input.roles, passwordHash: input.passwordHash };
    users.push(user);
    return user;
  }
  const { prisma } = await import("../prisma");
  const created = await prisma.user.create({
    data: { email: normalized, name: input.name, passwordHash: input.passwordHash, roles: input.roles as never },
  });
  return { id: created.id, email: created.email, name: created.name, roles: created.roles, passwordHash: created.passwordHash };
}
