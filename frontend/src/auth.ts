import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

// Server-side calls use INTERNAL_API_URL (Docker network), browser calls use NEXT_PUBLIC_API_URL
const BACKEND_URL = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  pages: {
    signIn: "/",
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      // Exchange Google identity for backend JWT — on first sign-in OR self-heal when backendToken is missing on a later refresh.
      const isFirstSignIn = !!(account && profile)
      const needsSelfHeal = !token.backendToken && !!token.email && !!token.sub
      if (isFirstSignIn || needsSelfHeal) {
        const body = isFirstSignIn
          ? {
              google_id: account!.providerAccountId,
              email: profile!.email,
              name: profile!.name || "",
              picture: (profile as any).picture || "",
            }
          : {
              google_id: token.sub as string,
              email: token.email as string,
              name: (token.name as string) || "",
              picture: (token.picture as string) || "",
            }
        try {
          const res = await fetch(`${BACKEND_URL}/api/v1/auth/token`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          })
          if (res.ok) {
            const data = await res.json()
            token.backendToken = data.access_token
            token.role = data.role || "customer"
          } else {
            console.error(
              `Backend token exchange failed (${isFirstSignIn ? "first sign-in" : "self-heal"}): ` +
                `${res.status} ${res.statusText} from ${BACKEND_URL}/api/v1/auth/token`,
            )
          }
        } catch (e) {
          console.error("Failed to get backend token:", e)
        }
      }
      return token
    },
    async session({ session, token }) {
      (session as any).backendToken = token.backendToken;
      (session as any).role = token.role || "customer"
      return session
    },
  },
})
