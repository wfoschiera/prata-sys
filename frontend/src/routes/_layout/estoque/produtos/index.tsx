import { useQuery } from "@tanstack/react-query"
import {
  createFileRoute,
  Link,
  redirect,
  useNavigate,
} from "@tanstack/react-router"
import { Package, Plus } from "lucide-react"
import { z } from "zod"

import {
  FornecedoresService,
  type ProductCategory,
  ProductsService,
} from "@/client"
import { PredictionBadge } from "@/components/estoque/PredictionBadge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

const searchSchema = z.object({
  category: z
    .enum(["tubos", "conexoes", "bombas", "cabos", "outros"])
    .optional(),
  fornecedor_id: z.string().optional(),
})

type SearchParams = z.infer<typeof searchSchema>

export const Route = createFileRoute("/_layout/estoque/produtos/")({
  validateSearch: searchSchema,
  component: ProdutosList,
  beforeLoad: async ({ context }: { context: any }) => {
    const user = context?.user
    if (!user) return
    if (!user.is_superuser && !user.permissions?.includes("view_estoque")) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Produtos - Estoque - Prata Sys" }],
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

function ProdutosTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

function ProdutosList() {
  const { user: currentUser } = useAuth()
  const isAdmin = currentUser?.is_superuser || currentUser?.role === "admin"

  const navigate = useNavigate()
  const { category, fornecedor_id } = Route.useSearch()

  const { data: products, isLoading } = useQuery({
    queryKey: ["products", category, fornecedor_id],
    queryFn: () =>
      ProductsService.listProducts({
        category: category ?? undefined,
        fornecedorId: fornecedor_id ?? undefined,
      }),
  })

  const { data: fornecedores } = useQuery({
    queryKey: ["fornecedores"],
    queryFn: () => FornecedoresService.listFornecedores({}),
  })

  function updateSearch(updates: Partial<SearchParams>) {
    void navigate({
      to: "/estoque/produtos",
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      search: (prev: any) => ({ ...prev, ...updates }) as any,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Produtos</h1>
          <p className="text-muted-foreground">
            Catálogo de produtos e histórico de estoque
          </p>
        </div>
        {isAdmin && (
          <Button asChild>
            <Link to="/estoque/produtos/new">
              <Plus className="mr-2 h-4 w-4" />
              Adicionar Produto
            </Link>
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select
          value={category ?? "all"}
          onValueChange={(val) =>
            updateSearch({
              category: val === "all" ? undefined : (val as ProductCategory),
            })
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as categorias</SelectItem>
            {ALL_CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {CATEGORY_LABELS[cat]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={fornecedor_id ?? "all"}
          onValueChange={(val) =>
            updateSearch({ fornecedor_id: val === "all" ? undefined : val })
          }
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Fornecedor" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os fornecedores</SelectItem>
            {(fornecedores ?? []).map((f) => (
              <SelectItem key={f.id} value={f.id}>
                {f.company_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {(category || fornecedor_id) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              void navigate({ to: "/estoque/produtos", search: {} as any })
            }
          >
            Limpar filtros
          </Button>
        )}
      </div>

      {isLoading ? (
        <ProdutosTableSkeleton />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Categoria / Tipo</TableHead>
              <TableHead>Fornecedor</TableHead>
              <TableHead className="text-right">Preço Unit.</TableHead>
              <TableHead>Previsão</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!products || products.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="py-8 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center gap-2">
                    <Package className="h-8 w-8 text-muted-foreground/50" />
                    Nenhum produto cadastrado.
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              products.map((product) => (
                <TableRow
                  key={product.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    void navigate({
                      to: "/estoque/produtos/$productId",
                      params: { productId: product.id },
                    })
                  }
                >
                  <TableCell className="font-medium">{product.name}</TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-0.5">
                      <Badge variant="secondary" className="w-fit text-xs">
                        {CATEGORY_LABELS[product.product_type.category]}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {product.product_type.name}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {product.fornecedor?.company_name ?? "—"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {Number(product.unit_price).toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </TableCell>
                  <TableCell>
                    <PredictionBadge productId={product.id} />
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
