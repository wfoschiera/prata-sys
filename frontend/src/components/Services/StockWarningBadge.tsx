import { AlertTriangle } from "lucide-react"

interface StockWarningBadgeProps {
  hasStockWarning: boolean
  compact?: boolean
}

const StockWarningBadge = ({
  hasStockWarning,
  compact = false,
}: StockWarningBadgeProps) => {
  if (!hasStockWarning) return null

  if (compact) {
    return (
      <span
        title="Materiais insuficientes no estoque"
        className="inline-flex items-center text-amber-600 dark:text-amber-500"
      >
        <AlertTriangle className="h-3.5 w-3.5" />
      </span>
    )
  }

  return (
    <div className="flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-300">
      <AlertTriangle className="h-4 w-4 shrink-0" />
      <span className="text-sm font-medium">
        Materiais insuficientes no estoque
      </span>
    </div>
  )
}

export default StockWarningBadge
