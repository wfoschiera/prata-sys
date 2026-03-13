import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Trash2, X } from "lucide-react"
import { useState } from "react"

import {
  type CategoriaTransacao,
  type TipoTransacao,
  TransacoesService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import AddTransacao from "./AddTransacao"
import {
  CATEGORIA_LABELS,
  EXPENSE_CATEGORIES,
  formatBRL,
  INCOME_CATEGORIES,
} from "./constants"
import EditTransacao from "./EditTransacao"

function hasPerm(
  permissions: string[] | undefined,
  isSuperuser: boolean | undefined,
  perm: string,
): boolean {
  if (isSuperuser) return true
  return permissions?.includes(perm) ?? false
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split("-")
  return `${day}/${month}/${year}`
}

interface TransacoesTableProps {
  tipoFilter?: TipoTransacao
}

interface Filters {
  tipo: string
  categoria: string
  dataInicio: string
  dataFim: string
}

const TransacoesTable = ({ tipoFilter }: TransacoesTableProps) => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const canManage = hasPerm(
    user?.permissions,
    user?.is_superuser,
    "manage_financeiro",
  )

  const [filters, setFilters] = useState<Filters>({
    tipo: tipoFilter ?? "",
    categoria: "",
    dataInicio: "",
    dataFim: "",
  })

  const queryParams = {
    tipo: (filters.tipo || undefined) as TipoTransacao | undefined,
    categoria: (filters.categoria || undefined) as
      | CategoriaTransacao
      | undefined,
    dataInicio: filters.dataInicio || undefined,
    dataFim: filters.dataFim || undefined,
    skip: 0,
    limit: 100,
  }

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["transacoes", queryParams],
    queryFn: () => TransacoesService.readTransacoes(queryParams),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      TransacoesService.deleteTransacao({ transacaoId: id }),
    onSuccess: () => {
      showSuccessToast("Transação excluída com sucesso")
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["transacoes"] })
    },
  })

  const categoriasDoFiltro =
    filters.tipo === "receita"
      ? INCOME_CATEGORIES
      : filters.tipo === "despesa"
        ? EXPENSE_CATEGORIES
        : [...INCOME_CATEGORIES, ...EXPENSE_CATEGORIES]

  const handleClearFilters = () => {
    setFilters({
      tipo: tipoFilter ?? "",
      categoria: "",
      dataInicio: "",
      dataFim: "",
    })
  }

  const transacoes = data?.data ?? []

  return (
    <div className="flex flex-col gap-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-end gap-3">
        {!tipoFilter && (
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium">Tipo</span>
            <Select
              value={filters.tipo}
              onValueChange={(val) =>
                setFilters((f) => ({
                  ...f,
                  tipo: val === "all" ? "" : val,
                  categoria: "",
                }))
              }
            >
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="receita">Receita</SelectItem>
                <SelectItem value="despesa">Despesa</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium">Categoria</span>
          <Select
            value={filters.categoria}
            onValueChange={(val) =>
              setFilters((f) => ({ ...f, categoria: val === "all" ? "" : val }))
            }
          >
            <SelectTrigger className="w-52">
              <SelectValue placeholder="Todas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              {categoriasDoFiltro.map((cat) => (
                <SelectItem key={cat} value={cat}>
                  {CATEGORIA_LABELS[cat]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium">De</span>
          <Input
            type="date"
            className="w-40"
            value={filters.dataInicio}
            onChange={(e) =>
              setFilters((f) => ({ ...f, dataInicio: e.target.value }))
            }
          />
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium">Até</span>
          <Input
            type="date"
            className="w-40"
            value={filters.dataFim}
            onChange={(e) =>
              setFilters((f) => ({ ...f, dataFim: e.target.value }))
            }
          />
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleClearFilters}
          className="flex items-center gap-1"
        >
          <X className="h-3 w-3" />
          Limpar
        </Button>

        <div className="ml-auto">
          {canManage && (
            <AddTransacao tipoFixo={tipoFilter} onSuccess={() => refetch()} />
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead>Descrição</TableHead>
              <TableHead>Contraparte</TableHead>
              <TableHead className="text-right">Valor</TableHead>
              {canManage && <TableHead className="w-24">Ações</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-28" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20 ml-auto" />
                  </TableCell>
                  {canManage && (
                    <TableCell>
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                  )}
                </TableRow>
              ))
            ) : transacoes.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={canManage ? 7 : 6}
                  className="h-24 text-center text-muted-foreground"
                >
                  Nenhuma transação encontrada
                </TableCell>
              </TableRow>
            ) : (
              transacoes.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="whitespace-nowrap">
                    {formatDate(t.data_competencia)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={t.tipo === "receita" ? "default" : "destructive"}
                      className={
                        t.tipo === "receita"
                          ? "bg-green-100 text-green-800 hover:bg-green-100"
                          : undefined
                      }
                    >
                      {t.tipo === "receita" ? "Receita" : "Despesa"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {CATEGORIA_LABELS[t.categoria] ?? t.categoria}
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {t.descricao ?? "-"}
                  </TableCell>
                  <TableCell>{t.nome_contraparte ?? "-"}</TableCell>
                  <TableCell className="text-right font-medium whitespace-nowrap">
                    {formatBRL(t.valor)}
                  </TableCell>
                  {canManage && (
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <EditTransacao
                          transacao={t}
                          onSuccess={() => refetch()}
                        />
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Confirmar exclusão</DialogTitle>
                              <DialogDescription>
                                Tem certeza que deseja excluir esta transação?
                                Esta ação não pode ser desfeita.
                              </DialogDescription>
                            </DialogHeader>
                            <DialogFooter>
                              <DialogClose asChild>
                                <Button variant="outline">Cancelar</Button>
                              </DialogClose>
                              <LoadingButton
                                variant="destructive"
                                loading={deleteMutation.isPending}
                                onClick={() => deleteMutation.mutate(t.id)}
                              >
                                Excluir
                              </LoadingButton>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

export default TransacoesTable
