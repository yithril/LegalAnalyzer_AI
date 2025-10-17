'use client'

import { useSession, signIn, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"

export function useAuth() {
  const { data: session, status, update } = useSession()
  const router = useRouter()

  const login = async (provider: string, credentials?: Record<string, string>) => {
    const result = await signIn(provider, {
      ...credentials,
      redirect: false,
    })
    
    if (result?.error) {
      throw new Error(result.error)
    }
    
    if (result?.ok) {
      router.push("/dashboard")
      router.refresh()
    }
  }

  const logout = async () => {
    await signOut({ redirect: false })
    router.push("/")
    router.refresh()
  }

  return {
    session,
    user: session?.user,
    isAuthenticated: status === "authenticated",
    isLoading: status === "loading",
    login,
    logout,
    update,
  }
}

