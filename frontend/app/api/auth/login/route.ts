import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();

  // ???: ???? docker ?????? ??? ???? ??? API
  const apiBase =
    process.env.NEXT_PUBLIC_API_URL || "http://revolution-x-api:8000";

  // ???? ?????? ??? ???? ??? backend ??????? ????:
  // ?????? /api/v1/auth/login ?? /api/v1/auth/token
  const r = await fetch(`${apiBase}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const txt = await r.text();
    return NextResponse.json({ error: txt || "Login failed" }, { status: r.status });
  }

  const data = await r.json();
  // ????? data.access_token
  const token = data?.access_token;

  if (!token) {
    return NextResponse.json(
      { error: "Missing access_token from API" },
      { status: 500 }
    );
  }

  const res = NextResponse.json({ ok: true, data });

  // ??? ?? ????? ???? ?????? middleware ????
  res.cookies.set("revolution_x_token", token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false, // ?????? true ??? https
    path: "/",
  });

  return res;
}