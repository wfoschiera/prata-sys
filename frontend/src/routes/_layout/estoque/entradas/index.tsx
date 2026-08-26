import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { useState } from "react"
import { EntradasEstoqueService, FornecedoresService } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { pageTitle } from "@/config/brand"

export const Route = createFileRoute("/_layout/estoque/entradas/")({
  component: EntradasList,
  head: () => ({
    meta: [{ title: pageTitle("Entradas de Estoque") }],
  }),
})

const brl = (v: string | number) =>
  Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })

const formatDate = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("pt-BR")

function EntradasList() {
  const [fornecedorId, setFornecedorId] = useState<string>("all")
  const [dataInicio, setDataInicio] = useState("")
  const [dataFim, setDataFim] = useState("")

  const { data: fornecedores } = useQuery({
    queryKey: ["fornecedores"],
    queryFn: () => FornecedoresService.listFornecedores({}),
  })

  const { data: entradas, isLoading } = useQuery({
    queryKey: ["entradas-estoque", fornecedorId, dataInicio, dataFim],
    queryFn: () =>
      EntradasEstoqueService.listEntradasEstoque({
        fornecedorId: fornecedorId === "all" ? undefined : fornecedorId,
        dataInicio: dataInicio || undefined,
        dataFim: dataFim || undefined,
      }),
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Entradas de Estoque
          </h1>
          <p className="text-muted-foreground">
            Entregas recebidas e o custo real de aquisição de cada uma
          </p>
        </div>
        <Button asChild>
          <Link to="/estoque/entradas/new">
            <Plus className="mr-1.5 h-4 w-4" />
            Nova Entrada
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="fornecedor">Fornecedor</Label>
          <Select value={fornecedorId} onValueChange={setFornecedorId}>
            <SelectTrigger id="fornecedor">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {(fornecedores ?? []).map((f) => (
                <SelectItem key={f.id} value={f.id}>
                  {f.company_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="inicio">De</Label>
          <Input
            id="inicio"
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="fim">Até</Label>
          <Input
            id="fim"
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
          />
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Fornecedor</TableHead>
            <TableHead>Documento</TableHead>
            <TableHead className="text-right">Produtos</TableHead>
            <TableHead className="text-right">Ajustes</TableHead>
            <TableHead className="text-right">Total real</TableHead>
            <TableHead>Financeiro</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={7} className="text-muted-foreground">
                Carregando...
              </TableCell>
            </TableRow>
          )}
          {!isLoading && (entradas ?? []).length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-muted-foreground">
                Nenhuma entrada registrada
              </TableCell>
            </TableRow>
          )}
          {(entradas ?? []).map((e) => (
            <TableRow key={e.id}>
              <TableCell>
                <Link
                  to="/estoque/entradas/$entradaId"
                  params={{ entradaId: e.id }}
                  className="font-medium hover:underline"
                >
                  {formatDate(e.data_entrada)}
                </Link>
              </TableCell>
              <TableCell>{e.fornecedor?.company_name ?? "—"}</TableCell>
              <TableCell>{e.numero_documento ?? "—"}</TableCell>
              <TableCell className="text-right">
                {brl(e.total_produtos)}
              </TableCell>
              <TableCell className="text-right">
                {brl(e.total_ajustes)}
              </TableCell>
              <TableCell className="text-right font-medium">
                {brl(e.total_real)}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {e.transacao_id ? "Lançado" : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
