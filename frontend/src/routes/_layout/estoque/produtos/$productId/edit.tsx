import { useQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"

import { ProductsService } from "@/client"
import { ProductForm } from "@/components/estoque/ProductForm"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute(
  "/_layout/estoque/produtos/$productId/edit",
)({
  component: EditProduto,
  beforeLoad: async ({
    context,
    params,
  }: {
    context: any
    params: { productId: string }
  }) => {
    const user = context?.user
    if (!user) return
    if (!user.is_superuser && user.role !== "admin") {
      throw redirect({
        to: "/estoque/produtos/$productId",
        params: { productId: params.productId },
      })
    }
  },
  head: () => ({
    meta: [{ title: "Editar Produto - Estoque - Prata Sys" }],
  }),
})

function EditProduto() {
  const { productId } = Route.useParams()

  const { data: product, isLoading } = useQuery({
    queryKey: ["products", productId],
    queryFn: () => ProductsService.getProduct({ productId }),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 max-w-2xl">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex flex-col gap-6">
        <p className="text-muted-foreground">Produto não encontrado.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Editar Produto</h1>
        <p className="text-muted-foreground">{product.name}</p>
      </div>
      <ProductForm product={product} />
    </div>
  )
}
