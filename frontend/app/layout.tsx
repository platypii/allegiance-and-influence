import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "How To Win Friends and Influence Agents",
  description: "A game of human-machine influence",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
