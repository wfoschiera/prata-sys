import { createFileRoute, redirect } from "@tanstack/react-router"

import { UsersService } from "@/client"
import TransacoesTable from "@/components/Financeiro/TransacoesTable"

export const Route = createFileRoute("/_layout/financeiro/transacoes")({
  component: Transacoes,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser && !user.permissions?.includes("view_financeiro")) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Transações - prata-sys" }],
  }),
})

function Transacoes() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Transações</h1>
        <p className="text-muted-foreground">Histórico financeiro completo</p>
      </div>
      <TransacoesTable />
    </div>
  )
}
