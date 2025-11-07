"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { MessageSquare, Layers, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const links = [
  { href: "/", label: "Single Inference", icon: MessageSquare },
  { href: "/batch", label: "Batch Inference", icon: Layers },
  { href: "/configuration", label: "Configuration", icon: Settings },
]

export function Nav() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-border bg-card">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold">
              Enter QA System
            </Link>
            <div className="flex items-center gap-1">
              {links.map((link) => {
                const Icon = link.icon
                const isActive = pathname === link.href
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {link.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
