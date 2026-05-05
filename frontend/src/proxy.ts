import { auth } from "@/auth"
import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export default auth((req) => {
  const isLoggedIn = !!req.auth
  const isProtected = req.nextUrl.pathname.startsWith("/chat") ||
                      req.nextUrl.pathname.startsWith("/dashboard") ||
                      req.nextUrl.pathname.startsWith("/status")

  if (isProtected && !isLoggedIn) {
    return NextResponse.redirect(new URL("/", req.nextUrl.origin))
  }

  // Dashboard requires officer role
  if (req.nextUrl.pathname.startsWith("/dashboard")) {
    const role = (req.auth as any)?.role
    if (role !== "officer") {
      return NextResponse.redirect(new URL("/chat", req.nextUrl.origin))
    }
  }
})

export const config = {
  matcher: ["/chat/:path*", "/dashboard/:path*", "/status/:path*"],
}
