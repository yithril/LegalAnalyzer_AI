"use client"

import { useSession, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { useEffect, useState } from "react"

export default function DashboardPage() {
  const { data: session, status } = useSession({
    required: true,
    onUnauthenticated() {
      router.push("/login")
    },
  })
  const router = useRouter()
  const [apiResponse, setApiResponse] = useState<string | null>(null)

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const testProtectedEndpoint = async () => {
    try {
      const res = await fetch("http://localhost:8000/cases", {
        method: "GET",
        credentials: "include", // Important: send cookies with session token
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (res.ok) {
        const data = await res.json()
        setApiResponse(`✅ Success! Fetched ${data.length} cases`)
      } else {
        setApiResponse(`❌ Error: ${res.status} ${res.statusText}`)
      }
    } catch (error) {
      setApiResponse(`❌ Error: ${error}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                LegalDocs AI
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                {session?.user?.name} ({session?.user?.role})
              </div>
              <button
                onClick={() => signOut({ callbackUrl: "/login" })}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-lg p-8"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Welcome, {session?.user?.name}!
          </h2>
          
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                User Information
              </h3>
              <div className="text-sm space-y-1 text-blue-800">
                <p><strong>Email:</strong> {session?.user?.email}</p>
                <p><strong>Name:</strong> {session?.user?.name}</p>
                <p><strong>Role:</strong> {session?.user?.role}</p>
                <p><strong>User ID:</strong> {session?.user?.id}</p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="font-semibold text-gray-900 mb-4">
                Test Protected API Endpoint
              </h3>
              <button
                onClick={testProtectedEndpoint}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/30"
              >
                Fetch Cases (Protected Endpoint)
              </button>
              
              {apiResponse && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <p className="text-sm font-mono">{apiResponse}</p>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
