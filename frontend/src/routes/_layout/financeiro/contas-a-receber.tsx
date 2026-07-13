import { createFileRoute, redirect } from "@tanstack/react-router"
import { UsersService } from "@/client"
import TransacoesTable from "@/components/Financeiro/TransacoesTable"
import { pageTitle } from "@/config/brand"

export const Route = createFileRoute("/_layout/financeiro/contas-a-receber")({
  component: ContasAReceber,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("view_contas_receber")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: pageTitle("Receitas") }],
  }),
})

function ContasAReceber() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Receitas</h1>
        <p className="text-muted-foreground">
          Histórico de receitas registradas
        </p>
      </div>
      <TransacoesTable tipoFilter="receita" />
    </div>
  )
}
