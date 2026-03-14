import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createFileRoute,
  Link,
  redirect,
  useNavigate,
} from "@tanstack/react-router"
import { ArrowLeft, Edit, Plus } from "lucide-react"
import { useState } from "react"

import {
  type ProductItemCreate,
  type ProductItemStatus,
  ProductItemsService,
  ProductsService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
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

export const Route = createFileRoute("/_layout/estoque/produtos/$productId/")({
  component: ProductDetail,
  beforeLoad: async ({ context }: { context: any }) => {
    const user = context?.user
    if (!user) return
    if (!user.is_superuser && !user.permissions?.includes("view_estoque")) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Produto - Estoque - Prata Sys" }],
  }),
})

const CATEGORY_LABELS: Record<string, string> = {
  tubos: "Tubos",
  conexoes: "Conexões",
  bombas: "Bombas",
  cabos: "Cabos",
  outros: "Outros",
}

const STATUS_LABELS: Record<ProductItemStatus, string> = {
  em_estoque: "Em Estoque",
  reservado: "Reservado",
  utilizado: "Utilizado",
}

const STATUS_VARIANTS: Record<
  ProductItemStatus,
  "default" | "secondary" | "outline"
> = {
  em_estoque: "default",
  reservado: "outline",
  utilizado: "secondary",
}

function PredictionCard({ productId }: { productId: string }) {
  const { data: prediction, isLoading } = useQuery({
    queryKey: ["product-prediction", productId],
    queryFn: () => ProductsService.getProductPrediction({ productId }),
  })

  if (isLoading) return <Skeleton className="h-24 w-full" />

  if (!prediction) return null

  const {
    level,
    days_to_stockout,
    em_estoque_qty,
    reservado_qty,
    avg_daily_consumption,
  } = prediction

  const colorMap: Record<string, string> = {
    green: "border-green-300 bg-green-50",
    yellow: "border-yellow-300 bg-yellow-50",
    red: "border-red-300 bg-red-50",
  }

  const badgeColorMap: Record<string, string> = {
    green: "bg-green-100 text-green-800",
    yellow: "bg-yellow-100 text-yellow-800",
    red: "bg-red-100 text-red-800",
  }

  const cardClass = colorMap[level] ?? colorMap.green
  const badgeClass = badgeColorMap[level] ?? badgeColorMap.green

  return (
    <Card className={`border ${cardClass}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Previsão de Estoque</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${badgeClass}`}
          >
            {days_to_stockout !== null && days_to_stockout !== undefined
              ? `${days_to_stockout} dias`
              : "Sem previsão"}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Em Estoque</p>
            <p className="font-semibold">
              {Number(em_estoque_qty).toLocaleString("pt-BR")}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Reservado</p>
            <p className="font-semibold">
              {Number(reservado_qty).toLocaleString("pt-BR")}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Consumo/dia</p>
            <p className="font-semibold">
              {avg_daily_consumption
                ? Number(avg_daily_consumption).toLocaleString("pt-BR", {
                    maximumFractionDigits: 2,
                  })
                : "—"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface AddItemModalProps {
  productId: string
  isOpen: boolean
  onClose: () => void
}

function AddItemModal({ productId, isOpen, onClose }: AddItemModalProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [quantity, setQuantity] = useState<number>(0)

  const mutation = useMutation({
    mutationFn: (data: ProductItemCreate) =>
      ProductItemsService.createProductItem({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Entrada de estoque adicionada")
      queryClient.invalidateQueries({ queryKey: ["product-items", productId] })
      queryClient.invalidateQueries({
        queryKey: ["product-prediction", productId],
      })
      queryClient.invalidateQueries({ queryKey: ["estoque", "dashboard"] })
      onClose()
      setQuantity(0)
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Adicionar Entrada de Estoque</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="quantity">Quantidade *</Label>
            <Input
              id="quantity"
              type="number"
              step="0.0001"
              min="0.0001"
              placeholder="0"
              value={quantity || ""}
              onChange={(e) => setQuantity(e.target.valueAsNumber)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <LoadingButton
            loading={mutation.isPending}
            disabled={!quantity || quantity <= 0}
            onClick={() => mutation.mutate({ product_id: productId, quantity })}
          >
            Adicionar
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ProductDetail() {
  const { productId } = Route.useParams()
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const isAdmin = currentUser?.is_superuser || currentUser?.role === "admin"
  const [addItemOpen, setAddItemOpen] = useState(false)

  const { data: product, isLoading: productLoading } = useQuery({
    queryKey: ["products", productId],
    queryFn: () => ProductsService.getProduct({ productId }),
  })

  const { data: items, isLoading: itemsLoading } = useQuery({
    queryKey: ["product-items", productId],
    queryFn: () => ProductsService.getProductItems({ productId }),
  })

  if (productLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex flex-col gap-6">
        <p className="text-muted-foreground">Produto não encontrado.</p>
        <Button variant="ghost" asChild className="w-fit">
          <Link to="/estoque/produtos">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Back + header */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <Button
            variant="ghost"
            size="sm"
            asChild
            className="w-fit -ml-2 mb-1"
          >
            <Link to="/estoque/produtos">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Produtos
            </Link>
          </Button>
          <h1 className="text-2xl font-bold tracking-tight">{product.name}</h1>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              {CATEGORY_LABELS[product.product_type.category]}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {product.product_type.name} ·{" "}
              {product.product_type.unit_of_measure}
            </span>
          </div>
        </div>
        {isAdmin && (
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              void navigate({
                to: "/estoque/produtos/$productId/edit",
                params: { productId },
              })
            }
          >
            <Edit className="mr-2 h-4 w-4" />
            Editar
          </Button>
        )}
      </div>

      {/* Product details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Detalhes do Produto</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Preço Unitário</span>
              <span className="font-semibold">
                {Number(product.unit_price).toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Fornecedor</span>
              <span>{product.fornecedor?.company_name ?? "—"}</span>
            </div>
            {product.description && (
              <div>
                <p className="text-muted-foreground mb-1">Descrição</p>
                <p>{product.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <PredictionCard productId={productId} />
      </div>

      {/* Stock history */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Histórico de Estoque</h2>
          {isAdmin && (
            <Button size="sm" onClick={() => setAddItemOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Entrada
            </Button>
          )}
        </div>

        {itemsLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Quantidade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Serviço</TableHead>
                <TableHead>Data</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!items || items.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="py-6 text-center text-muted-foreground"
                  >
                    Nenhuma entrada de estoque registrada.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono">
                      {Number(item.quantity).toLocaleString("pt-BR")}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANTS[item.status]}>
                        {STATUS_LABELS[item.status]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.service_id ? (
                        <span className="font-mono text-xs">
                          {item.service_id.slice(0, 8)}…
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {item.created_at
                        ? new Date(item.created_at).toLocaleDateString("pt-BR")
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>

      <AddItemModal
        productId={productId}
        isOpen={addItemOpen}
        onClose={() => setAddItemOpen(false)}
      />
    </div>
  )
}
