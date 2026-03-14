import { useQueries } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"

import { TransacoesService, UsersService } from "@/client"
import { formatBRL } from "@/components/Financeiro/constants"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

const MES_ABBR = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
]

export const Route = createFileRoute("/_layout/financeiro/")({
  component: FinanceiroDashboard,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser && !user.permissions?.includes("view_financeiro")) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Financeiro - prata-sys" }],
  }),
})

function getLast6Months(): Array<{ ano: number; mes: number }> {
  const months: Array<{ ano: number; mes: number }> = []
  const now = new Date()
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({ ano: d.getFullYear(), mes: d.getMonth() + 1 })
  }
  return months
}

function FinanceiroDashboard() {
  const months = getLast6Months()

  const results = useQueries({
    queries: months.map(({ ano, mes }) => ({
      queryKey: ["resumo-mensal", ano, mes],
      queryFn: () => TransacoesService.getResumoMensal({ ano, mes }),
    })),
  })

  const isLoading = results.some((r) => r.isLoading)
  const resumos = results.map((r) => r.data)

  const currentResumo = resumos[resumos.length - 1]
  const currentReceitas = parseFloat(currentResumo?.total_receitas ?? "0")
  const currentDespesas = parseFloat(currentResumo?.total_despesas ?? "0")
  const currentLiquido = parseFloat(currentResumo?.resultado_liquido ?? "0")

  // For bar chart: compute max value across all months for scaling
  const allValues = resumos.flatMap((r) =>
    r ? [parseFloat(r.total_receitas), parseFloat(r.total_despesas)] : [0],
  )
  const maxValue = Math.max(...allValues, 1)

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Dashboard Financeiro
        </h1>
        <p className="text-muted-foreground">
          Visão geral das finanças do mês atual
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Receitas do Mês
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-2xl font-bold text-green-600">
                {formatBRL(currentReceitas)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Despesas do Mês
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-2xl font-bold text-red-600">
                {formatBRL(currentDespesas)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Resultado Líquido
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p
                className={`text-2xl font-bold ${
                  currentLiquido >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatBRL(currentLiquido)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bar chart — last 6 months */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Últimos 6 Meses</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-end gap-4 h-40">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="flex-1 h-full" />
              ))}
            </div>
          ) : (
            <div className="flex items-end gap-3 h-48">
              {months.map(({ ano, mes }, idx) => {
                const r = resumos[idx]
                const receitas = parseFloat(r?.total_receitas ?? "0")
                const despesas = parseFloat(r?.total_despesas ?? "0")
                const receitasH = (receitas / maxValue) * 100
                const despesasH = (despesas / maxValue) * 100
                return (
                  <div
                    key={`${ano}-${mes}`}
                    className="flex flex-col items-center flex-1 gap-1"
                  >
                    <div className="flex items-end gap-1 w-full h-40">
                      <div
                        className="flex-1 bg-green-500 rounded-t-sm min-h-[2px]"
                        style={{ height: `${receitasH}%` }}
                        title={`Receitas: ${formatBRL(receitas)}`}
                      />
                      <div
                        className="flex-1 bg-red-400 rounded-t-sm min-h-[2px]"
                        style={{ height: `${despesasH}%` }}
                        title={`Despesas: ${formatBRL(despesas)}`}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {MES_ABBR[mes - 1]}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
          <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-sm bg-green-500" />
              Receitas
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded-sm bg-red-400" />
              Despesas
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
