import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, redirect } from "@tanstack/react-router"
import { ArrowRight, Package } from "lucide-react"

import { EstoqueService, type ProductCategory } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute("/_layout/estoque/")({
  component: EstoqueDashboard,
  beforeLoad: async ({ context }: { context: any }) => {
    const user = context?.user
    if (!user) {
      // Let parent layout handle auth
      return
    }
    if (!user.is_superuser && !user.permissions?.includes("view_estoque")) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Estoque - Prata Sys" }],
  }),
})

const CATEGORY_LABELS: Record<ProductCategory, string> = {
  tubos: "Tubos",
  conexoes: "Conexões",
  bombas: "Bombas",
  cabos: "Cabos",
  outros: "Outros",
}

const ALL_CATEGORIES: ProductCategory[] = [
  "tubos",
  "conexoes",
  "bombas",
  "cabos",
  "outros",
]

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-48 w-full" />
      ))}
    </div>
  )
}

function EstoqueDashboard() {
  const {
    data: dashboard,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["estoque", "dashboard"],
    queryFn: () => EstoqueService.getDashboard(),
  })

  // Create a map from category to dashboard item for easy lookup
  const dashboardMap = new Map(
    (dashboard ?? []).map((item) => [item.category, item]),
  )

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Estoque</h1>
          <p className="text-muted-foreground">
            Visão geral do estoque por categoria
          </p>
        </div>
        <DashboardSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Estoque</h1>
        </div>
        <p className="text-destructive">Erro ao carregar dados do estoque.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Estoque</h1>
          <p className="text-muted-foreground">
            Visão geral do estoque por categoria
          </p>
        </div>
        <Button asChild>
          <Link to="/estoque/produtos">Ver Todos os Produtos</Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {ALL_CATEGORIES.map((category) => {
          const item = dashboardMap.get(category)
          const emEstoque = item?.em_estoque_total ?? "0"
          const reservado = item?.reservado_total ?? "0"
          const utilizado = item?.utilizado_total ?? "0"

          return (
            <Card key={category} className="flex flex-col">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Package className="h-4 w-4 text-muted-foreground" />
                  {CATEGORY_LABELS[category]}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 flex-1">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Em Estoque
                    </p>
                    <Badge
                      variant="secondary"
                      className="text-sm font-bold px-2 py-1"
                    >
                      {Number(emEstoque).toLocaleString("pt-BR")}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Reservado
                    </p>
                    <Badge
                      variant="outline"
                      className="text-sm font-bold px-2 py-1"
                    >
                      {Number(reservado).toLocaleString("pt-BR")}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Utilizado
                    </p>
                    <Badge
                      variant="secondary"
                      className="text-sm font-bold px-2 py-1 text-muted-foreground"
                    >
                      {Number(utilizado).toLocaleString("pt-BR")}
                    </Badge>
                  </div>
                </div>
                <div className="mt-auto pt-2">
                  <Button variant="ghost" size="sm" asChild className="w-full">
                    <Link to="/estoque/produtos" search={{ category }}>
                      Ver Produtos
                      <ArrowRight className="ml-2 h-3 w-3" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
