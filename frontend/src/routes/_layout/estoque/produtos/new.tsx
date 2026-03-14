import { createFileRoute, redirect } from "@tanstack/react-router"

import { ProductForm } from "@/components/estoque/ProductForm"

export const Route = createFileRoute("/_layout/estoque/produtos/new")({
  component: NewProduto,
  beforeLoad: async ({ context }: { context: any }) => {
    const user = context?.user
    if (!user) return
    if (!user.is_superuser && user.role !== "admin") {
      throw redirect({ to: "/estoque/produtos" })
    }
  },
  head: () => ({
    meta: [{ title: "Novo Produto - Estoque - Prata Sys" }],
  }),
})

function NewProduto() {
  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Novo Produto</h1>
        <p className="text-muted-foreground">
          Adicione um novo produto ao catálogo
        </p>
      </div>
      <ProductForm />
    </div>
  )
}
