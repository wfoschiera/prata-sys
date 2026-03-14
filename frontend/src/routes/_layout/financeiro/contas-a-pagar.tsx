import { createFileRoute, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import TransacoesTable from "@/components/Financeiro/TransacoesTable"

export const Route = createFileRoute("/_layout/financeiro/contas-a-pagar")({
  component: ContasAPagar,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("view_contas_pagar")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Despesas - prata-sys" }],
  }),
})

function ContasAPagar() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Despesas</h1>
        <p className="text-muted-foreground">
          Histórico de despesas registradas
        </p>
      </div>
      <TransacoesTable tipoFilter="despesa" />
    </div>
  )
}
