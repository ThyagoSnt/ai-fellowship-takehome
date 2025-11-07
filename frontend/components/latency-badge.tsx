import { Badge } from "@/components/ui/badge"
import { Clock } from "lucide-react"

interface LatencyBadgeProps {
  latency: number
}

export function LatencyBadge({ latency }: LatencyBadgeProps) {
  const getVariant = () => {
    if (latency < 1000) return "default"
    if (latency < 3000) return "secondary"
    return "destructive"
  }

  return (
    <Badge variant={getVariant()} className="gap-1">
      <Clock className="h-3 w-3" />
      {latency}ms
    </Badge>
  )
}
