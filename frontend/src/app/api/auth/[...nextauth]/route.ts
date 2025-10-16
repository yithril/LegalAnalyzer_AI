import NextAuth from "next-auth"
import type { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

// Debug: Check the secret
const secret = process.env.NEXTAUTH_SECRET
console.log('[NextAuth] NEXTAUTH_SECRET FULL:', secret)

export const authOptions: NextAuthOptions = {
  secret: secret,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "user@test.com" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          // Call your FastAPI backend login endpoint
          const res = await fetch("http://localhost:8000/api/auth/login", {
            method: "POST",
            headers: { 
              "Content-Type": "application/json" 
            },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })
          
          if (!res.ok) {
            return null
          }

          const user = await res.json()
          
          // Return user object with required fields
          if (user) {
            return {
              id: user.id.toString(),
              email: user.email,
              name: user.name,
              role: user.role,
            }
          }
          
          return null
        } catch (error) {
          console.error("Auth error:", error)
          return null
        }
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  cookies: {
    sessionToken: {
      name: `next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: 'none', // Required for cross-origin requests
        path: '/',
        secure: true, // Required when sameSite is 'none'
      },
    },
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      // On sign in, add user info to token
      if (user) {
        token.id = user.id
        token.role = user.role
      }
      return token
    },
    async session({ session, token }) {
      // Add user info to session
      if (session.user) {
        session.user.id = token.id as string
        session.user.role = token.role as string
      }
      return session
    }
  }
}

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }

