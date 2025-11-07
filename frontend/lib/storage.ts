const HISTORY_KEY = "pdf-extraction-history"
const API_BASE_URL_KEY = "api-base-url"

export interface HistoryItem {
  id: string
  timestamp: number
  request: any
  response: any
  latency: number
  status: number
}

export function getHistory(): HistoryItem[] {
  if (typeof window === "undefined") return []
  const stored = localStorage.getItem(HISTORY_KEY)
  return stored ? JSON.parse(stored) : []
}

export function addToHistory(item: Omit<HistoryItem, "id" | "timestamp">) {
  const history = getHistory()
  const newItem: HistoryItem = {
    ...item,
    id: Math.random().toString(36).substring(7),
    timestamp: Date.now(),
  }
  const updated = [newItem, ...history].slice(0, 10)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
  return newItem
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY)
}

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
  }
  const stored = localStorage.getItem(API_BASE_URL_KEY)
  return stored || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
}

export function setApiBaseUrl(url: string) {
  localStorage.setItem(API_BASE_URL_KEY, url)
}
