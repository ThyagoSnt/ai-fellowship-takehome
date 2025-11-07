"use client"

import type React from "react"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Nav } from "@/components/nav"
import { JsonViewer } from "@/components/json-viewer"
import { JsonEditor } from "@/components/json-editor"
import { LatencyBadge } from "@/components/latency-badge"
import { inferPath } from "@/lib/api"
import { addToHistory } from "@/lib/storage"
import { EXAMPLE_LABEL, EXAMPLE_SCHEMA, EXAMPLE_PDF_PATH } from "@/lib/examples"
import { useToast } from "@/hooks/use-toast"
import { Send, Sparkles, Trash2 } from "lucide-react"

export default function HomePage() {
  const [label, setLabel] = useState("")
  const [pdfPath, setPdfPath] = useState("")
  const [schema, setSchema] = useState(JSON.stringify(EXAMPLE_SCHEMA, null, 2))
  const [result, setResult] = useState<any>(null)
  const { toast } = useToast()

  const inferMutation = useMutation({
    mutationFn: async () => {
      let parsedSchema
      try {
        parsedSchema = JSON.parse(schema)
      } catch (e) {
        throw new Error("Invalid JSON schema")
      }
      return inferPath({ label, extraction_schema: parsedSchema, pdf_path: pdfPath })
    },
    onSuccess: (result) => {
      setResult(result)

      addToHistory({
        request: {
          label,
          extraction_schema: JSON.parse(schema),
          pdf_path: pdfPath,
        },
        response: result.data,
        latency: result.latency,
        status: result.status,
      })

      toast({ title: "Inference completed" })
    },
    onError: (error: any) => {
      toast({ title: "Inference failed", description: error.message, variant: "destructive" })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!label) {
      toast({ title: "Label is required", variant: "destructive" })
      return
    }

    if (!pdfPath) {
      toast({ title: "PDF path is required", variant: "destructive" })
      return
    }

    try {
      JSON.parse(schema)
    } catch (e) {
      toast({ title: "Invalid JSON schema", variant: "destructive" })
      return
    }

    inferMutation.mutate()
  }

  const handleUseExample = () => {
    setLabel(EXAMPLE_LABEL)
    setPdfPath(EXAMPLE_PDF_PATH)
    setSchema(JSON.stringify(EXAMPLE_SCHEMA, null, 2))
    toast({ title: "Example loaded" })
  }

  const handleClear = () => {
    setLabel("")
    setPdfPath("")
    setSchema("") // Clear the schema JSON editor as well
    setResult(null)
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Nav />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Enter Question Answering System</h1>
            <p className="text-muted-foreground">Single PDF extraction interface</p>
          </div>

          <div className="grid gap-6">
            <Card className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="label">Label</Label>
                    <Input
                      id="label"
                      value={label}
                      onChange={(e) => setLabel(e.target.value)}
                      placeholder="e.g., carteira_oab"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="pdf-path">PDF Path</Label>
                    <Input
                      id="pdf-path"
                      value={pdfPath}
                      onChange={(e) => setPdfPath(e.target.value)}
                      placeholder="./path/to/file.pdf"
                    />
                  </div>
                </div>

                <JsonEditor
                  value={schema}
                  onChange={setSchema}
                  showLabel={false}
                  placeholder="Enter extraction schema..."
                />

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={handleUseExample}>
                      <Sparkles className="h-4 w-4 mr-1" />
                      Use Example
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={handleClear}>
                      <Trash2 className="h-4 w-4 mr-1" />
                      Clear
                    </Button>
                  </div>
                  <Button type="submit" disabled={inferMutation.isPending}>
                    <Send className="h-4 w-4 mr-1" />
                    {inferMutation.isPending ? "Processing..." : "Extract"}
                  </Button>
                </div>
              </form>
            </Card>

            {result && (
              <Card className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Extraction Result</h3>
                    <div className="flex items-center gap-2">
                      <Badge variant={result.status === 200 ? "default" : "destructive"}>HTTP {result.status}</Badge>
                      <LatencyBadge latency={result.latency} />
                    </div>
                  </div>
                  <Separator />
                  <JsonViewer data={result.data} />
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
