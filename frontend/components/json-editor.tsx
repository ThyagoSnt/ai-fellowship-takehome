"use client"

import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Wand2 } from "lucide-react"

interface JsonEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
  showLabel?: boolean
}

export function JsonEditor({ value, onChange, placeholder, error, showLabel = true }: JsonEditorProps) {
  const handleBeautify = () => {
    try {
      const parsed = JSON.parse(value)
      onChange(JSON.stringify(parsed, null, 2))
    } catch (e) {
      // Invalid JSON, do nothing
    }
  }

  return (
    <div className="space-y-2">
      {showLabel && (
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Extraction Schema (JSON)</label>
          <Button type="button" size="sm" variant="ghost" onClick={handleBeautify} className="h-7 gap-1">
            <Wand2 className="h-3 w-3" />
            Beautify
          </Button>
        </div>
      )}
      {!showLabel && (
        <div className="flex items-center justify-end">
          <Button type="button" size="sm" variant="ghost" onClick={handleBeautify} className="h-7 gap-1">
            <Wand2 className="h-3 w-3" />
            Beautify
          </Button>
        </div>
      )}
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="font-mono text-sm min-h-[200px]"
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
