import { Badge } from "@/components/ui/badge"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"

interface HealthStatusProps {
  status: string
  label?: string
}

export function HealthStatus({ status, label }: HealthStatusProps) {
  const isHealthy = status === "healthy" || status === "ok"
  const isLoading = status === "loading"

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-sm text-muted-foreground">{label}:</span>}
      <Badge variant={isHealthy ? "default" : "destructive"} className="gap-1">
        {isLoading ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : isHealthy ? (
          <CheckCircle2 className="h-3 w-3" />
        ) : (
          <XCircle className="h-3 w-3" />
        )}
        {status}
      </Badge>
    </div>
  )
}
