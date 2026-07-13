import { Link } from "@tanstack/react-router"

import { APP_NAME } from "@/config/brand"
import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

// Short mark derived from the brand name (e.g. "Prata Poços" -> "PP").
const APP_INITIALS = APP_NAME.split(/\s+/)
  .map((word) => word[0]?.toUpperCase() ?? "")
  .join("")
  .slice(0, 2)

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const wordmark = (
    <span
      className={cn(
        "font-semibold tracking-tight whitespace-nowrap",
        className,
      )}
    >
      {APP_NAME}
    </span>
  )

  const mark = (
    <span className={cn("font-bold tracking-tight", className)}>
      {APP_INITIALS}
    </span>
  )

  const content =
    variant === "responsive" ? (
      <>
        <span className="group-data-[collapsible=icon]:hidden">{wordmark}</span>
        <span className="hidden group-data-[collapsible=icon]:inline">
          {mark}
        </span>
      </>
    ) : variant === "full" ? (
      wordmark
    ) : (
      mark
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
