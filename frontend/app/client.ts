"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { Character } from "./characters"

export type Seat = "player_red" | "player_blue"
export interface Chat {
  target: string | null
  messages: { name: string; content: string }[]
  done: boolean
  join_opponent: boolean
  work: { request_id: string; status: "pending" | "succeeded" | "failed" | "cancelled" | "interrupted"; error: string | null } | null
}
export interface Game {
  schema_version: "2"
  rules_version: string
  mode: "scripted"
  id: string
  version: number
  config: { num_agents: number; num_rounds: number; seed: number }
  phase: "lobby" | "selecting" | "conversing" | "round_complete" | "finished"
  round_number: number
  players: Record<Seat, boolean>
  agents: (Character & { side: number })[]
  conversations: Record<Seat, Chat>
  pairings: [string, string][]
  history: { round_number: number; summaries: { pair: [string, string]; text: string }[]; scores: Record<Seat, number> }[]
  scores: Record<Seat, number>
  winner: Seat | "tie" | null
  you: Seat | null
}
export type Action = { kind: "select"; target: string } | { kind: "message"; text: string } | { kind: "done" } | { kind: "advance" } | { kind: "retry" } | { kind: "cancel" }

function randomId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(24)), byte => byte.toString(16).padStart(2, "0")).join("")
}

class ApiError extends Error {
  constructor(message: string, public code: string) { super(message) }
}

async function request<T>(path: string, token: string | null, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  const data = await response.json()
  if (!response.ok) throw new ApiError(data.error?.message || "The server could not accept that request.", data.error?.code || "invalid_request")
  return data as T
}

export function useGame() {
  const [gameId, setGameId] = useState<string | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [game, setGame] = useState<Game | null>(null)
  const [connection, setConnection] = useState("Connecting")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const pending = useRef(false)
  const current = useRef<Game | null>(null)

  const accept = useCallback((next: Game) => {
    setGame(previous => {
      if (previous && previous.id === next.id && previous.version > next.version) return previous
      current.current = next
      return next
    })
  }, [])

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("game")
    setGameId(id)
    if (id) setToken(sessionStorage.getItem(`player:${id}`))
    else setConnection("Local")
  }, [])

  useEffect(() => {
    if (!gameId) return
    let stopped = false
    let socket: WebSocket | undefined
    let timer: ReturnType<typeof setTimeout>
    let attempts = 0
    request<Game>(`/api/games/${gameId}`, token).then(g => { if (!stopped) accept(g) }).catch(e => { if (!stopped) setError(e.message) })
    const connect = () => {
      if (stopped) return
      setConnection(attempts ? "Reconnecting" : "Connecting")
      socket = new WebSocket(`${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/api/games/${gameId}/live`)
      socket.onopen = () => socket?.send(JSON.stringify({ authorization: token ? `Bearer ${token}` : null }))
      socket.onmessage = event => {
        if (stopped) return
        attempts = 0
        setConnection("Connected")
        accept(JSON.parse(event.data))
      }
      socket.onclose = event => {
        if (stopped) return
        if (event.code === 1008) { setConnection("Disconnected"); return }
        setConnection("Reconnecting")
        timer = setTimeout(connect, Math.min(1000 * 2 ** attempts++, 10000))
      }
    }
    connect()
    return () => { stopped = true; clearTimeout(timer); socket?.close() }
  }, [gameId, token, accept])

  async function operation<T>(fn: () => Promise<T>): Promise<T | undefined> {
    if (pending.current) return
    pending.current = true
    setBusy(true)
    setError("")
    try { return await fn() } catch (e) {
      setError(e instanceof Error ? e.message : "Connection lost. Try again.")
      if (e instanceof ApiError && e.code === "stale_version" && gameId) {
        try { accept(await request<Game>(`/api/games/${gameId}`, token)) } catch { /* connection status handles reconnect */ }
      }
    } finally { pending.current = false; setBusy(false) }
  }

  async function create(config: Game["config"]) {
    return operation(async () => {
      const next = await request<Game>("/api/games", null, config)
      history.replaceState(null, "", `?game=${next.id}`)
      setToken(null)
      accept(next)
      setGameId(next.id)
    })
  }

  async function join(seat: Seat) {
    if (!gameId) return
    return operation(async () => {
      // Save before sending so a lost response can be retried safely.
      const key = sessionStorage.getItem(`player:${gameId}`) || randomId()
      sessionStorage.setItem(`player:${gameId}`, key)
      const next = await request<Game>(`/api/games/${gameId}/join`, key, { seat })
      accept(next)
      setToken(key)
    })
  }

  async function command(action: Action): Promise<boolean> {
    const snapshot = current.current
    if (!snapshot || !token) return false
    const body = { ...action, command_id: randomId(), expected_version: snapshot.version }
    return (await operation(async () => {
      let next: Game
      try { next = await request<Game>(`/api/games/${snapshot.id}/commands`, token, body) }
      catch (e) {
        // Transport errors have uncertain outcomes; retry with exactly the same command ID.
        if (!(e instanceof TypeError)) throw e
        next = await request<Game>(`/api/games/${snapshot.id}/commands`, token, body)
      }
      accept(next)
      return true
    })) || false
  }

  async function replay() {
    if (!gameId || !token) return
    return operation(() => request<{ frames: Game[] }>(`/api/games/${gameId}/replay`, token))
  }
  return { game, connection, error, busy, create, join, command, replay }
}
