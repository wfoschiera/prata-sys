import { useQuery } from "@tanstack/react-query"
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { Building2, Plus, Search, X } from "lucide-react"
import { useState } from "react"

import {
  type FornecedorCategoryEnum,
  FornecedoresService,
  UsersService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/fornecedores/")({
  component: Fornecedores,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("view_fornecedores")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Fornecedores - Prata Sys" }],
  }),
})

const CATEGORY_LABELS: Record<FornecedorCategoryEnum, string> = {
  tubos: "Tubos",
  conexoes: "Conexões",
  bombas: "Bombas",
  cabos: "Cabos",
  outros: "Outros",
}

const ALL_CATEGORIES: FornecedorCategoryEnum[] = [
  "tubos",
  "conexoes",
  "bombas",
  "cabos",
  "outros",
]

function FornecedoresTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

function Fornecedores() {
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const canManage =
    currentUser?.is_superuser ||
    currentUser?.permissions?.includes("manage_fornecedores")

  const [search, setSearch] = useState("")
  const [activeCategory, setActiveCategory] =
    useState<FornecedorCategoryEnum | null>(null)

  const { data: fornecedores, isLoading } = useQuery({
    queryKey: ["fornecedores", search, activeCategory],
    queryFn: () =>
      FornecedoresService.listFornecedores({
        search: search || undefined,
        category: activeCategory ?? undefined,
      }),
  })

  const toggleCategory = (cat: FornecedorCategoryEnum) => {
    setActiveCategory((prev) => (prev === cat ? null : cat))
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Fornecedores</h1>
          <p className="text-muted-foreground">
            Gerencie os fornecedores e contatos
          </p>
        </div>
        {canManage && (
          <Button
            onClick={() =>
              navigate({
                to: "/fornecedores/$fornecedorId",
                params: { fornecedorId: "new" },
              })
            }
          >
            <Plus className="mr-2 h-4 w-4" />
            Novo Fornecedor
          </Button>
        )}
      </div>

      {/* Search + category filters */}
      <div className="flex flex-col gap-3">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar por nome…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {ALL_CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => toggleCategory(cat)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                activeCategory === cat
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-background text-muted-foreground hover:border-primary hover:text-foreground"
              }`}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
          {activeCategory && (
            <button
              type="button"
              onClick={() => setActiveCategory(null)}
              className="text-xs text-muted-foreground underline"
            >
              Limpar filtro
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <FornecedoresTableSkeleton />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Empresa</TableHead>
              <TableHead>CNPJ</TableHead>
              <TableHead>Categorias</TableHead>
              <TableHead>Contatos</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!fornecedores || fornecedores.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="py-8 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center gap-2">
                    <Building2 className="h-8 w-8 text-muted-foreground/50" />
                    Nenhum fornecedor cadastrado.
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              fornecedores.map((f) => (
                <TableRow
                  key={f.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    navigate({
                      to: "/fornecedores/$fornecedorId",
                      params: { fornecedorId: f.id },
                    })
                  }
                >
                  <TableCell className="font-medium">
                    {f.company_name}
                  </TableCell>
                  <TableCell className="font-mono text-sm text-muted-foreground">
                    {f.cnpj ?? "—"}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {f.categories.length === 0 ? (
                        <span className="text-muted-foreground">—</span>
                      ) : (
                        f.categories.map((cat) => (
                          <Badge
                            key={cat}
                            variant="secondary"
                            className="text-xs"
                          >
                            {CATEGORY_LABELS[cat]}
                          </Badge>
                        ))
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {f.contatos.length}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
