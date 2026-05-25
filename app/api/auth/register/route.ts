import { NextResponse } from "next/server";
import { z } from "zod";
import { cookies } from "next/headers";
import { createUser, findUserByEmail } from "@/lib/auth/users";
import { hashPassword } from "@/lib/auth/password";
import { SESSION_COOKIE, cookieOptions, signSession } from "@/lib/auth/session";
import { firstRoleHome } from "@/lib/auth/guards";

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
  password: z.string().min(8),
  roles: z.array(z.enum(["CLIENT", "DESIGNER", "MAKER"])).min(1),
});

export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { email, name, password, roles } = parsed.data;

  if (await findUserByEmail(email)) {
    return NextResponse.json({ error: "Email già registrata" }, { status: 409 });
  }

  const passwordHash = await hashPassword(password);
  const user = await createUser({ email, name, passwordHash, roles });

  const token = await signSession({ id: user.id, email: user.email, name: user.name, roles: user.roles });
  (await cookies()).set(SESSION_COOKIE, token, cookieOptions());

  return NextResponse.json(
    {
      ok: true,
      user: { id: user.id, email: user.email, name: user.name, roles: user.roles },
      redirect: firstRoleHome(user.roles),
    },
    { status: 201 },
  );
}
