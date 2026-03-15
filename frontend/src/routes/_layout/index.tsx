import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { DollarSign, Drill, TrendingUp, Wrench } from "lucide-react"

import { DashboardService, type WeeklyOperationalSummary } from "@/client"
import { formatBRL } from "@/components/Financeiro/constants"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [{ title: "Dashboard - Prata Sys" }],
  }),
})

function getCurrentISOWeek(): number {
  const now = new Date()
  const startOfYear = new Date(now.getFullYear(), 0, 1)
  const dayOfYear =
    Math.floor((now.getTime() - startOfYear.getTime()) / 86400000) + 1
  return Math.ceil(dayOfYear / 7)
}

function KpiCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-24 mb-1" />
        <Skeleton className="h-3 w-20" />
      </CardContent>
    </Card>
  )
}

function ChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-48" />
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-1 h-40">
          {Array.from({ length: 20 }).map((_, i) => (
            <Skeleton key={i} className="flex-1 h-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function OperationalDashboard() {
  const ano = new Date().getFullYear()
  const currentWeek = getCurrentISOWeek()

  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard", "operational", ano],
    queryFn: () => DashboardService.getOperationalDashboard({ ano }),
  })

  const weeks: WeeklyOperationalSummary[] = data?.weeks ?? []

  // Current week KPIs
  const currentWeekData = weeks.find((w) => w.week_number === currentWeek)
  const repairsCount = currentWeekData?.repairs_count ?? 0
  const drillingsCount = currentWeekData?.drillings_count ?? 0
  const drillingMeters = parseFloat(
    String(currentWeekData?.drilling_meters ?? "0"),
  )
  const profit = parseFloat(String(currentWeekData?.profit ?? "0"))

  // Chart: max value across all weeks for scaling
  const maxCount = Math.max(
    ...weeks.map((w) => Math.max(w.repairs_count, w.drillings_count)),
    1,
  )

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Dashboard Operacional
          </h1>
          <p className="text-muted-foreground">Semana atual · {ano}</p>
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <KpiCardSkeleton key={i} />
          ))}
        </div>
        <ChartSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-2xl font-bold tracking-tight">
          Dashboard Operacional
        </h1>
        <p className="text-destructive">Erro ao carregar dados do dashboard.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Dashboard Operacional
        </h1>
        <p className="text-muted-foreground">
          Semana {currentWeek} · {ano}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="hover:shadow-md transition-shadow">
          <Link to="/services" className="block">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                Reparos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{repairsCount}</p>
              <p className="text-xs text-muted-foreground mt-1">
                concluídos esta semana
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <Link to="/services" className="block">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Drill className="h-4 w-4" />
                Perfurações
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{drillingsCount}</p>
              <p className="text-xs text-muted-foreground mt-1">
                concluídas esta semana
              </p>
            </CardContent>
          </Link>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Metros Perfurados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {drillingMeters.toLocaleString("pt-BR", {
                maximumFractionDigits: 1,
              })}
              <span className="text-lg font-medium text-muted-foreground ml-1">
                m
              </span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              perfurados esta semana
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Lucro Semanal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-3xl font-bold ${
                profit >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {formatBRL(profit)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              receitas − despesas
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Weekly bar chart — all 52 weeks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Serviços por Semana · {ano}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {weeks.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Nenhum dado disponível para {ano}.
            </p>
          ) : (
            <>
              <div className="flex items-end gap-[2px] h-40 overflow-x-auto pb-1">
                {Array.from({ length: 52 }, (_, i) => i + 1).map((wk) => {
                  const w = weeks.find((x) => x.week_number === wk)
                  const repairs = w?.repairs_count ?? 0
                  const drillings = w?.drillings_count ?? 0
                  const repairsH = (repairs / maxCount) * 100
                  const drillingsH = (drillings / maxCount) * 100
                  const isCurrentWeek = wk === currentWeek
                  return (
                    <div
                      key={wk}
                      className={`flex flex-col items-center flex-1 min-w-[10px] gap-0.5 ${
                        isCurrentWeek ? "opacity-100" : "opacity-70"
                      }`}
                      title={`S${wk}: ${repairs} reparos, ${drillings} perfurações`}
                    >
                      <div className="flex items-end gap-[1px] w-full h-36">
                        <div
                          className={`flex-1 rounded-t-sm min-h-[1px] ${
                            isCurrentWeek ? "bg-blue-500" : "bg-blue-400"
                          }`}
                          style={{ height: `${repairsH}%` }}
                        />
                        <div
                          className={`flex-1 rounded-t-sm min-h-[1px] ${
                            isCurrentWeek ? "bg-orange-500" : "bg-orange-400"
                          }`}
                          style={{ height: `${drillingsH}%` }}
                        />
                      </div>
                      {isCurrentWeek && (
                        <span className="text-[9px] text-muted-foreground leading-none">
                          {wk}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="inline-block h-3 w-3 rounded-sm bg-blue-400" />
                  Reparos
                </span>
                <span className="flex items-center gap-1">
                  <span className="inline-block h-3 w-3 rounded-sm bg-orange-400" />
                  Perfurações
                </span>
                <span className="flex items-center gap-1 ml-auto">
                  <span className="inline-block h-3 w-3 rounded-sm bg-blue-500 ring-1 ring-offset-1 ring-blue-500" />
                  Semana atual
                </span>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  const canViewDashboard =
    currentUser?.is_superuser ||
    currentUser?.permissions?.includes("view_dashboard")

  if (!canViewDashboard) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold tracking-tight">
          Bem-vindo, {currentUser?.full_name || currentUser?.email}!
        </h1>
        <p className="text-muted-foreground">
          Use o menu lateral para navegar pelo sistema.
        </p>
      </div>
    )
  }

  return <OperationalDashboard />
}
