import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { access_token } = await req.json().catch(() => ({}));

  if (!access_token || typeof access_token !== "string") {
    return NextResponse.json({ error: "access_token is required" }, { status: 400 });
  }

  const res = NextResponse.json({ ok: true });

  // ???? ????? ????? ?? middleware.ts
  res.cookies.set("revolution_x_token", access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false, // true ?? https
    path: "/",
  });

  return res;
}