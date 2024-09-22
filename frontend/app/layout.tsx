import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Allegiance and Influence",
  description: "A game of human-machine influence",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/images/favicon.png" />
      </head>
      <body>
        {children}
      </body>
    </html>
  )
}
