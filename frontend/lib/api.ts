import { z } from "zod"
import { getApiBaseUrl } from "./storage"

export const extractionSchemaSchema = z.record(z.string())

export const inferRequestSchema = z.object({
  label: z.string().min(1, "Label is required"),
  extraction_schema: extractionSchemaSchema,
  pdf_path: z.string().min(1, "PDF path is required"),
})

export const batchRequestSchema = z.object({
  json_path: z.string().min(1, "JSON path is required"),
  pdfs_root_path: z.string().min(1, "PDFs root path is required"),
})

export type InferRequest = z.infer<typeof inferRequestSchema>
export type BatchRequest = z.infer<typeof batchRequestSchema>

export interface LocalHealthResponse {
  status: string
  version: string
  uptime_s: number
  env_ready: {
    MODAL_EXTRACTION_URL: boolean
    MODAL_HEALTH_CHECK_URL: boolean
    AUTH_TOKEN: boolean
  }
}

export interface RemoteHealthResponse {
  status: "ok" | "error" | "unconfigured"
  latency_ms?: number
  remote?: any
  detail?: string
}

export interface CombinedHealthResponse {
  local_status: string
  remote_status: RemoteHealthResponse
  local: LocalHealthResponse
}

export interface InferResponse {
  [key: string]: any
}

export interface BatchStartResponse {
  status: string
  job_id: string
  total: number
}

export interface BatchResult {
  filename: string
  status: "success" | "error"
  data?: InferResponse
  error?: string
  latency_ms?: number
}

export async function checkLocalHealth(): Promise<{ data: LocalHealthResponse; latency: number }> {
  const start = Date.now()
  const response = await fetch(`${getApiBaseUrl()}/health/local`)
  const latency = Date.now() - start

  if (!response.ok) {
    throw new Error("Local health check failed")
  }

  const data = await response.json()
  return { data, latency }
}

export async function checkRemoteHealth(): Promise<{ data: RemoteHealthResponse; latency: number }> {
  const start = Date.now()
  try {
    const response = await fetch(`${getApiBaseUrl()}/health/remote`)
    const latency = Date.now() - start
    const data = await response.json()

    // If response is not ok but we got JSON, it's likely the "unconfigured" case
    if (!response.ok && response.status === 503) {
      return { data: { status: "unconfigured", ...data }, latency }
    }

    return { data, latency }
  } catch (error) {
    const latency = Date.now() - start
    return {
      data: {
        status: "error",
        detail: error instanceof Error ? error.message : "Unknown error",
      },
      latency,
    }
  }
}

export async function checkHealth(): Promise<{ data: CombinedHealthResponse; latency: number }> {
  const start = Date.now()
  const response = await fetch(`${getApiBaseUrl()}/health`)
  const latency = Date.now() - start

  if (!response.ok) {
    throw new Error("Health check failed")
  }

  const data = await response.json()
  return { data, latency }
}

export async function inferPath(
  request: InferRequest,
): Promise<{ data: InferResponse; latency: number; status: number }> {
  const start = Date.now()
  const response = await fetch(`${getApiBaseUrl()}/infer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  const latency = Date.now() - start

  const data = await response.json()
  return { data, latency, status: response.status }
}

export async function startBatch(request: BatchRequest): Promise<BatchStartResponse> {
  const response = await fetch(`${getApiBaseUrl()}/batch/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error("Failed to start batch processing")
  }

  return response.json()
}

export function getBatchResultUrl(jobId: string, stream = false): string {
  if (stream) {
    return `${getApiBaseUrl()}/batch/stream/${jobId}`
  }
  return `${getApiBaseUrl()}/batch/result/${jobId}`
}

export function getBatchDownloadUrl(jobId: string): string {
  return `${getApiBaseUrl()}/batch/result/${jobId}/download`
}

export { getApiBaseUrl }
