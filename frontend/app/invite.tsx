"use client"

import { useEffect, useRef, useState } from "react"

export default function Invite({ gameId, expanded = false }: { gameId: string; expanded?: boolean }) {
  const [url, setUrl] = useState("")
  const [copied, setCopied] = useState(false)
  const [manual, setManual] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => {
    const invite = new URL("/", location.href)
    invite.searchParams.set("game", gameId)
    setUrl(invite.href)
    setCopied(false)
  }, [gameId])
  useEffect(() => { if (manual) { input.current?.focus(); input.current?.select() } }, [manual])
  return <div className="invite">
    <button disabled={!url} onClick={async () => {
      try {
        if (!navigator.clipboard) throw new Error("Clipboard unavailable")
        await navigator.clipboard.writeText(url)
        setCopied(true)
      } catch { setCopied(false); setManual(true) }
    }}>{copied ? "Link copied" : "Copy invite link"}</button>
    {(expanded || manual) && <label>
      {manual ? "Select and copy this session link:" : "Session invite link"}
      <input ref={input} aria-label="Session invite link" readOnly value={url} onFocus={e => e.target.select()} />
    </label>}
  </div>
}
