import type { Metadata } from "next"
import { Inter } from "next/font/google"
import AuthProvider from "@/components/providers/SessionProvider"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "LegalDocs AI",
  description: "AI-powered legal document analysis",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
