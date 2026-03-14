import { useQuery } from "@tanstack/react-query"
import { ProductsService } from "@/client"

interface PredictionBadgeProps {
  productId: string
}

export function PredictionBadge({ productId }: PredictionBadgeProps) {
  const { data: prediction, isLoading } = useQuery({
    queryKey: ["product-prediction", productId],
    queryFn: () => ProductsService.getProductPrediction({ productId }),
    staleTime: 60_000,
  })

  if (isLoading) {
    return <span className="text-xs text-muted-foreground">…</span>
  }

  if (!prediction) {
    return <span className="text-muted-foreground">—</span>
  }

  const { level, days_to_stockout } = prediction

  const variantMap: Record<string, string> = {
    green: "bg-green-100 text-green-800 border-green-300",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-300",
    red: "bg-red-100 text-red-800 border-red-300",
  }

  const colorClass = variantMap[level] ?? variantMap.green

  const label =
    days_to_stockout !== null && days_to_stockout !== undefined
      ? `${days_to_stockout}d`
      : "—"

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${colorClass}`}
    >
      {label}
    </span>
  )
}
