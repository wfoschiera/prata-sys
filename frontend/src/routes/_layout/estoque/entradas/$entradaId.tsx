import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { EntradasEstoqueService } from "@/client"
import { AJUSTE_LABELS } from "@/components/estoque/custoAquisicao"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { pageTitle } from "@/config/brand"

export const Route = createFileRoute("/_layout/estoque/entradas/$entradaId")({
  component: EntradaDetail,
  head: () => ({
    meta: [{ title: pageTitle("Entrada de Estoque") }],
  }),
})

const brl = (v: string | number | null | undefined) =>
  v === null || v === undefined
    ? "—"
    : Number(v).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
      })

const formatDate = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("pt-BR")

function EntradaDetail() {
  const { entradaId } = Route.useParams()

  const { data: entrada, isLoading } = useQuery({
    queryKey: ["entradas-estoque", entradaId],
    queryFn: () => EntradasEstoqueService.getEntradaEstoque({ entradaId }),
  })

  if (isLoading) {
    return <p className="text-muted-foreground">Carregando...</p>
  }
  if (!entrada) {
    return <p className="text-muted-foreground">Entrada não encontrada</p>
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/estoque/entradas">
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            Voltar
          </Link>
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          Entrada de {formatDate(entrada.data_entrada)}
        </h1>
      </div>

      <div className="grid grid-cols-3 gap-4 rounded-md border p-4 text-sm">
        <div>
          <p className="text-muted-foreground">Fornecedor</p>
          <p className="font-medium">
            {entrada.fornecedor?.company_name ?? "—"}
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">Documento</p>
          <p className="font-medium">{entrada.numero_documento ?? "—"}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Despesa lançada</p>
          <p className="font-medium">{entrada.transacao_id ? "Sim" : "Não"}</p>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Itens</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Produto</TableHead>
              <TableHead className="text-right">Quantidade</TableHead>
              <TableHead className="text-right">Custo NF</TableHead>
              <TableHead className="text-right">Custo real</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(entrada.itens ?? []).map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.product?.name ?? "—"}</TableCell>
                <TableCell className="text-right">{item.quantity}</TableCell>
                <TableCell className="text-right">
                  {brl(item.custo_unitario_nf)}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {brl(item.custo_unitario_real)}
                </TableCell>
                <TableCell>{item.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Ajustes de custo</h2>
        {(entrada.ajustes ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nenhum ajuste — o custo real é igual ao valor da nota.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tipo</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead>Documento</TableHead>
                <TableHead>Observação</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(entrada.ajustes ?? []).map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{AJUSTE_LABELS[a.tipo] ?? a.tipo}</TableCell>
                  <TableCell className="text-right">{brl(a.valor)}</TableCell>
                  <TableCell>{a.documento_referencia ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {a.observacao ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <div className="rounded-md border p-4 space-y-2 max-w-sm ml-auto">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total dos produtos</span>
          <span>{brl(entrada.total_produtos)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Total de ajustes</span>
          <span>{brl(entrada.total_ajustes)}</span>
        </div>
        <div className="flex justify-between font-semibold border-t pt-2">
          <span>Total real</span>
          <span>{brl(entrada.total_real)}</span>
        </div>
      </div>

      {entrada.observacao && (
        <div className="rounded-md border p-4">
          <p className="text-sm text-muted-foreground">Observações</p>
          <p className="text-sm">{entrada.observacao}</p>
        </div>
      )}
    </div>
  )
}
