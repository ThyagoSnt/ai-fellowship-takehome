"use client"

import { useState } from "react"
import { Copy, Download, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useToast } from "@/hooks/use-toast"

interface JsonViewerProps {
  data: any
  filename?: string
}

export function JsonViewer({ data, filename = "data.json" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)
  const { toast } = useToast()

  const jsonString = JSON.stringify(data, null, 2)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast({ title: "Copied to clipboard" })
  }

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: "Downloaded successfully" })
  }

  const highlightJson = (json: string) => {
    return json
      .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
      .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
      .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
      .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
      .replace(/: null/g, ': <span class="json-null">null</span>')
  }

  return (
    <div className="relative">
      <div className="absolute right-2 top-2 flex gap-2">
        <Button size="sm" variant="secondary" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
        <Button size="sm" variant="secondary" onClick={handleDownload}>
          <Download className="h-4 w-4" />
        </Button>
      </div>
      <pre className="rounded-xl bg-muted p-4 pr-24 overflow-x-auto font-mono text-sm">
        <code dangerouslySetInnerHTML={{ __html: highlightJson(jsonString) }} />
      </pre>
    </div>
  )
}
