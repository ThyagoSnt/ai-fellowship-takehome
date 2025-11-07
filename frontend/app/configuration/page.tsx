"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Nav } from "@/components/nav"
import { LatencyBadge } from "@/components/latency-badge"
import { checkHealth, checkLocalHealth, checkRemoteHealth } from "@/lib/api"
import { getApiBaseUrl, setApiBaseUrl } from "@/lib/storage"
import { useToast } from "@/hooks/use-toast"
import { CheckCircle2, XCircle, AlertCircle, RefreshCw, Save } from "lucide-react"

export default function ConfigurationPage() {
  const [baseUrl, setBaseUrl] = useState(getApiBaseUrl())
  const { toast } = useToast()

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
    refetchInterval: 30000,
  })

  const localHealthQuery = useQuery({
    queryKey: ["health-local"],
    queryFn: checkLocalHealth,
    refetchInterval: 30000,
  })

  const remoteHealthQuery = useQuery({
    queryKey: ["health-remote"],
    queryFn: checkRemoteHealth,
    refetchInterval: 30000,
  })

  const handleSaveUrl = () => {
    setApiBaseUrl(baseUrl)
    toast({ title: "API URL saved", description: "The page will reload to apply changes." })
    setTimeout(() => window.location.reload(), 1000)
  }

  const handleRefresh = () => {
    healthQuery.refetch()
    localHealthQuery.refetch()
    remoteHealthQuery.refetch()
    toast({ title: "Health checks refreshed" })
  }

  const getStatusIcon = (status: string) => {
    if (status === "ok" || status === "healthy") return <CheckCircle2 className="h-4 w-4 text-green-500" />
    if (status === "unconfigured") return <AlertCircle className="h-4 w-4 text-yellow-500" />
    if (status === "error") return <XCircle className="h-4 w-4 text-red-500" />
    return <AlertCircle className="h-4 w-4 text-yellow-500" />
  }

  const getStatusVariant = (status: string): "default" | "destructive" | "secondary" => {
    if (status === "ok" || status === "healthy") return "default"
    if (status === "unconfigured") return "secondary"
    return "destructive"
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Nav />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Configuration</h1>
            <p className="text-muted-foreground">Configure API settings and monitor system health</p>
          </div>

          {/* API Configuration */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">API Settings</h2>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label htmlFor="base-url">FastAPI Base URL</Label>
                <div className="flex gap-2">
                  <Input
                    id="base-url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="flex-1"
                  />
                  <Button onClick={handleSaveUrl}>
                    <Save className="h-4 w-4 mr-1" />
                    Set API
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  Current: <code className="bg-muted px-2 py-1 rounded">{getApiBaseUrl()}</code>
                </p>
              </div>
            </div>
          </Card>

          {/* Health Checks */}
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Health Checks</h2>
                <Button variant="outline" size="sm" onClick={handleRefresh}>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Refresh
                </Button>
              </div>
              <Separator />

              {/* Combined Health */}
              <div className="space-y-3">
                <h3 className="font-medium">Combined Status</h3>
                {healthQuery.isLoading ? (
                  <div className="text-sm text-muted-foreground">Loading...</div>
                ) : healthQuery.error ? (
                  <Badge variant="destructive">Error: {(healthQuery.error as Error).message}</Badge>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(healthQuery.data?.data.local_status || "")}
                      <span className="font-medium">Local:</span>
                      <Badge>{healthQuery.data?.data.local_status}</Badge>
                      <LatencyBadge latency={healthQuery.data?.latency || 0} />
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(healthQuery.data?.data.remote_status.status || "")}
                      <span className="font-medium">Remote:</span>
                      <Badge>{healthQuery.data?.data.remote_status.status}</Badge>
                      {healthQuery.data?.data.remote_status.latency_ms && (
                        <LatencyBadge latency={healthQuery.data.data.remote_status.latency_ms} />
                      )}
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              {/* Local Health */}
              <div className="space-y-3">
                <h3 className="font-medium">Local Health</h3>
                {localHealthQuery.isLoading ? (
                  <div className="text-sm text-muted-foreground">Loading...</div>
                ) : localHealthQuery.error ? (
                  <Badge variant="destructive">Error: {(localHealthQuery.error as Error).message}</Badge>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(localHealthQuery.data?.data.status || "")}
                      <Badge>{localHealthQuery.data?.data.status}</Badge>
                      <LatencyBadge latency={localHealthQuery.data?.latency || 0} />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Version:</span>{" "}
                        <code className="bg-muted px-2 py-1 rounded">{localHealthQuery.data?.data.version}</code>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Uptime:</span>{" "}
                        <code className="bg-muted px-2 py-1 rounded">
                          {localHealthQuery.data?.data.uptime_s.toFixed(2)}s
                        </code>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-medium">Environment Variables:</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(localHealthQuery.data?.data.env_ready || {}).map(([key, value]) => (
                          <Badge key={key} variant={value ? "default" : "destructive"}>
                            {key}: {value ? "✓" : "✗"}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              {/* Remote Health */}
              <div className="space-y-3">
                <h3 className="font-medium">Remote Health (Modal)</h3>
                {remoteHealthQuery.isLoading ? (
                  <div className="text-sm text-muted-foreground">Loading...</div>
                ) : remoteHealthQuery.error ? (
                  <Badge variant="destructive">Error: {(remoteHealthQuery.error as Error).message}</Badge>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(remoteHealthQuery.data?.data.status || "")}
                      <Badge variant={getStatusVariant(remoteHealthQuery.data?.data.status || "")}>
                        {remoteHealthQuery.data?.data.status}
                      </Badge>
                      {remoteHealthQuery.data?.data.latency_ms && (
                        <LatencyBadge latency={remoteHealthQuery.data.data.latency_ms} />
                      )}
                    </div>
                    {remoteHealthQuery.data?.data.detail && (
                      <p className="text-sm text-muted-foreground">{remoteHealthQuery.data.data.detail}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}
