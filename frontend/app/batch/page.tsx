"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Nav } from "@/components/nav"
import { startBatch, getBatchResultUrl, getBatchDownloadUrl, getApiBaseUrl } from "@/lib/api"
import { EXAMPLE_BATCH_JSON_PATH, EXAMPLE_BATCH_PDFS_ROOT } from "@/lib/examples"
import { useToast } from "@/hooks/use-toast"
import { Play, Download, Copy, Sparkles, CheckCircle2, XCircle, Loader2, X } from "lucide-react"

interface SSEStartMessage {
  type: "start"
  job_id: string
  total: number
  processed: number
  status: "running"
}

interface SSEItemOkMessage {
  type: "item_ok"
  job_id: string
  index: number
  file_name: string
  response_ms: number
  filled_item: any
  processed: number
  total: number
  preview_download_path: string
}

interface SSEItemErrorMessage {
  type: "item_error"
  job_id: string
  index: number
  file_name: string
  response_ms: number
  error: string
  processed: number
  total: number
  preview_download_path: string
}

interface SSECompleteMessage {
  type: "complete"
  job_id: string
  status: "done"
  processed: number
  failed: number
  total: number
}

type SSEMessage = SSEStartMessage | SSEItemOkMessage | SSEItemErrorMessage | SSECompleteMessage

interface BatchRow {
  index: number
  file: string
  status: string
  response_ms?: number
  preview_download_path?: string
}

export default function BatchPage() {
  const [jsonPath, setJsonPath] = useState("")
  const [pdfsRootPath, setPdfsRootPath] = useState("")
  const [jobId, setJobId] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [processed, setProcessed] = useState(0)
  const [rows, setRows] = useState<BatchRow[]>([])
  const [done, setDone] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const { toast } = useToast()
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [])

  const handleStartBatch = async () => {
    if (!jsonPath || !pdfsRootPath) {
      toast({ title: "All fields are required", variant: "destructive" })
      return
    }

    try {
      setIsRunning(true)
      setDone(false)
      setRows([])
      setProcessed(0)

      const result = await startBatch({ pdfs_root_path: pdfsRootPath, json_path: jsonPath })
      setJobId(result.job_id)
      setTotal(result.total)

      const eventSource = new EventSource(getBatchResultUrl(result.job_id, true))
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const message: SSEMessage = JSON.parse(event.data)

          switch (message.type) {
            case "start":
              setTotal(message.total)
              setProcessed(0)
              break

            case "item_ok":
              setRows((prev) => [
                ...prev,
                {
                  index: message.index,
                  file: message.file_name,
                  status: "OK",
                  response_ms: message.response_ms,
                  preview_download_path: message.preview_download_path,
                },
              ])
              setProcessed(message.processed)
              break

            case "item_error":
              setRows((prev) => [
                ...prev,
                {
                  index: message.index,
                  file: message.file_name,
                  status: message.error,
                  response_ms: message.response_ms,
                  preview_download_path: message.preview_download_path,
                },
              ])
              setProcessed(message.processed)
              break

            case "complete":
              setDone(true)
              setIsRunning(false)
              eventSource.close()
              eventSourceRef.current = null
              toast({
                title: "Batch processing completed",
                description: `Processed ${message.processed} files, ${message.failed} failed`,
              })
              break
          }
        } catch (error) {
          console.error("[v0] Failed to parse SSE message:", error)
        }
      }

      eventSource.onerror = () => {
        if (!done) {
          toast({
            title: "Connection lost",
            description: "Stream closed before completion. Try again.",
            variant: "destructive",
          })
        }
        eventSource.close()
        eventSourceRef.current = null
        setIsRunning(false)
      }
    } catch (error: any) {
      toast({ title: "Failed to start batch", description: error.message, variant: "destructive" })
      setIsRunning(false)
    }
  }

  const handleLoadExample = () => {
    setJsonPath(EXAMPLE_BATCH_JSON_PATH)
    setPdfsRootPath(EXAMPLE_BATCH_PDFS_ROOT)
    toast({ title: "Example loaded" })
  }

  const handleClear = () => {
    setJsonPath("")
    setPdfsRootPath("")
    toast({ title: "Form cleared" })
  }

  const handleDownload = () => {
    if (!jobId) return
    window.open(getBatchDownloadUrl(jobId), "_blank")
  }

  const handleCopyToClipboard = async () => {
    if (!jobId) return

    try {
      const response = await fetch(getBatchResultUrl(jobId, false))
      const data = await response.json()
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      toast({ title: "Copied to clipboard" })
    } catch (error: any) {
      toast({ title: "Failed to copy", description: error.message, variant: "destructive" })
    }
  }

  const progressPercent = total > 0 ? (processed / total) * 100 : 0

  return (
    <div className="min-h-screen bg-background">
      <Nav />

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Batch Runner</h1>
            <p className="text-muted-foreground">Process multiple PDFs with live streaming updates</p>
          </div>

          <Card className="rounded-2xl">
            <CardHeader>
              <CardTitle>Batch Configuration</CardTitle>
              <CardDescription>Configure paths and start batch processing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pdfs-root">PDFs Root Path</Label>
                  <Input
                    id="pdfs-root"
                    value={pdfsRootPath}
                    onChange={(e) => setPdfsRootPath(e.target.value)}
                    placeholder="./files"
                    disabled={isRunning}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="json-path">Dataset JSON Path</Label>
                  <Input
                    id="json-path"
                    value={jsonPath}
                    onChange={(e) => setJsonPath(e.target.value)}
                    placeholder="./dataset.json"
                    disabled={isRunning}
                  />
                </div>
              </div>

              <Separator className="my-4" />

              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleLoadExample} disabled={isRunning}>
                    <Sparkles className="h-4 w-4 mr-1" />
                    Load Example
                  </Button>
                  <Button variant="outline" onClick={handleClear} disabled={isRunning}>
                    <X className="h-4 w-4 mr-1" />
                    Clear
                  </Button>
                </div>
                <Button onClick={handleStartBatch} disabled={isRunning}>
                  {isRunning ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-1" />
                      Start Batch
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {isRunning && (
            <Card className="rounded-2xl">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-mono">
                      {processed} / {total} ({progressPercent.toFixed(0)}%)
                    </span>
                  </div>
                  <Progress value={progressPercent} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {rows.length > 0 && (
            <Card className="rounded-2xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Live Results</CardTitle>
                    <CardDescription>
                      {rows.length} item(s) processed
                      {done && ` • ${rows.filter((r) => r.status === "OK").length} succeeded`}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopyToClipboard} disabled={!done}>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy Final JSON
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDownload} disabled={!done}>
                      <Download className="h-4 w-4 mr-1" />
                      Download Final JSON
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border overflow-hidden">
                  <Table>
                    <TableHeader className="sticky top-0 bg-muted/50">
                      <TableRow>
                        <TableHead className="w-16">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="w-32">Status</TableHead>
                        <TableHead className="w-32">Response Time</TableHead>
                        <TableHead className="w-24">Preview</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rows.map((row) => (
                        <TableRow key={row.index}>
                          <TableCell className="font-mono text-sm text-muted-foreground">{row.index}</TableCell>
                          <TableCell className="font-mono text-sm">{row.file}</TableCell>
                          <TableCell>
                            {row.status === "OK" ? (
                              <Badge variant="default" className="gap-1">
                                <CheckCircle2 className="h-3 w-3" />
                                OK
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="gap-1">
                                <XCircle className="h-3 w-3" />
                                ERR
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-sm text-muted-foreground">
                            {row.response_ms ? `${(row.response_ms / 1000).toFixed(2)}s` : "-"}
                          </TableCell>
                          <TableCell>
                            {row.preview_download_path && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(`${getApiBaseUrl()}${row.preview_download_path}`, "_blank")}
                                className="h-8 px-2"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}
