import { createFileRoute, redirect } from "@tanstack/react-router"
import { useState } from "react"
import { EntradaForm } from "@/components/estoque/EntradaForm"
import {
  ImportarNfeXml,
  type ImportPrefill,
} from "@/components/estoque/ImportarNfeXml"
import { pageTitle } from "@/config/brand"

export const Route = createFileRoute("/_layout/estoque/entradas/new")({
  component: NovaEntrada,
  beforeLoad: async ({ context }: { context: any }) => {
    const user = context?.user
    if (!user) return
    if (!user.is_superuser && user.role !== "admin") {
      throw redirect({ to: "/estoque/entradas" })
    }
  },
  head: () => ({
    meta: [{ title: pageTitle("Nova Entrada - Estoque") }],
  }),
})

function NovaEntrada() {
  const [prefill, setPrefill] = useState<ImportPrefill | null>(null)

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Nova Entrada de Estoque
        </h1>
        <p className="text-muted-foreground">
          Registre os itens recebidos e os ajustes que compõem o custo real de
          aquisição
        </p>
      </div>
      {!prefill && <ImportarNfeXml onApply={setPrefill} />}
      {prefill ? (
        <EntradaForm key={JSON.stringify(prefill)} initialValues={prefill} />
      ) : (
        <EntradaForm />
      )}
    </div>
  )
}
