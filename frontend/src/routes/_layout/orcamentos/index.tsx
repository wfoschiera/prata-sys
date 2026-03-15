import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Link, redirect } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { Suspense, useState } from "react"

import {
  type OrcamentoListRead,
  type OrcamentoStatus,
  OrcamentosService,
  UsersService,
} from "@/client"
import OrcamentoListFilters from "@/components/Orcamentos/OrcamentoListFilters"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { PaginationBar } from "@/components/ui/pagination-bar"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const PAGE_SIZE = 20

const STATUS_LABELS: Record<OrcamentoStatus, string> = {
  rascunho: "Rascunho",
  em_analise: "Em Análise",
  aprovado: "Aprovado",
  cancelado: "Cancelado",
}

const STATUS_VARIANTS: Record<
  OrcamentoStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  rascunho: "secondary",
  em_analise: "outline",
  aprovado: "default",
  cancelado: "destructive",
}

interface FilterValues {
  search?: string
  status?: OrcamentoStatus
  dataInicio?: string
  dataFim?: string
}

function getQueryOptions(page: number, filters: FilterValues) {
  return {
    queryFn: () =>
      OrcamentosService.listOrcamentos({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        search: filters.search,
        status: filters.status,
        dataInicio: filters.dataInicio,
        dataFim: filters.dataFim,
      }),
    queryKey: ["orcamentos", page, filters],
  }
}

export const Route = createFileRoute("/_layout/orcamentos/")({
  component: OrcamentoList,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("manage_orcamentos")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Orçamentos - Prata Sys" }],
  }),
})

function OrcamentoTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={`skel-${i}`} className="h-12 w-full" />
      ))}
    </div>
  )
}

interface TableContentProps {
  page: number
  filters: FilterValues
  onPageChange: (page: number) => void
}

function OrcamentoTableContent({
  page,
  filters,
  onPageChange,
}: TableContentProps) {
  const { data } = useSuspenseQuery(getQueryOptions(page, filters))

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Código</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead>Descrição</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Criado em</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="text-center text-muted-foreground py-8"
              >
                Nenhum orçamento encontrado.
              </TableCell>
            </TableRow>
          ) : (
            data.data.map((orc: OrcamentoListRead) => (
              <TableRow
                key={orc.id}
                className="cursor-pointer hover:bg-muted/50"
              >
                <TableCell>
                  <Link
                    to="/orcamentos/$orcamentoId"
                    params={{ orcamentoId: orc.id }}
                    className="font-mono text-xs text-primary hover:underline"
                  >
                    #{orc.ref_code}
                  </Link>
                </TableCell>
                <TableCell className="font-medium">
                  {orc.client?.name ?? "—"}
                </TableCell>
                <TableCell className="text-muted-foreground max-w-xs truncate">
                  {orc.description ?? "—"}
                </TableCell>
                <TableCell>
                  <Badge variant={STATUS_VARIANTS[orc.status]}>
                    {STATUS_LABELS[orc.status]}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {orc.created_at
                    ? new Date(orc.created_at).toLocaleDateString("pt-BR")
                    : "—"}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <PaginationBar
        page={page}
        pageSize={PAGE_SIZE}
        total={data.count}
        onPageChange={onPageChange}
      />
    </>
  )
}

function OrcamentoList() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<FilterValues>({})

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Orçamentos</h1>
          <p className="text-muted-foreground">
            Gerencie os orçamentos e propostas comerciais
          </p>
        </div>
        <Button asChild>
          <Link to="/orcamentos/new">
            <Plus className="mr-2 h-4 w-4" />
            Novo Orçamento
          </Link>
        </Button>
      </div>

      <OrcamentoListFilters
        filters={filters}
        onFiltersChange={(f) => {
          setFilters(f)
          setPage(1)
        }}
      />

      <Suspense fallback={<OrcamentoTableSkeleton />}>
        <OrcamentoTableContent
          page={page}
          filters={filters}
          onPageChange={setPage}
        />
      </Suspense>
    </div>
  )
}
