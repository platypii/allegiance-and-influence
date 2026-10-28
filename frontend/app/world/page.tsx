"use client"

import { useEffect } from "react"

// Preserve old bookmarks and session links without maintaining a second game route.
export default function WorldRedirect() {
  useEffect(() => { window.location.replace(`/${window.location.search}${window.location.hash}`) }, [])
  return <main><p>Opening the gathering… <a href="/">Continue to the game</a></p></main>
}
