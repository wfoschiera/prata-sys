import {
  ArrowDownCircle,
  ArrowUpCircle,
  Drill,
  Home,
  LayoutDashboard,
  Lock,
  Truck,
  UserSquare2,
  Users,
  Wallet,
} from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

function hasPerm(
  permissions: string[] | undefined,
  isSuperuser: boolean | undefined,
  perm: string,
): boolean {
  if (isSuperuser) return true
  return permissions?.includes(perm) ?? false
}

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const perms = currentUser?.permissions
  const su = currentUser?.is_superuser

  const items: Item[] = [
    ...(hasPerm(perms, su, "view_dashboard")
      ? [{ icon: Home, title: "Dashboard", path: "/" as const }]
      : []),
    ...(hasPerm(perms, su, "manage_clients")
      ? [{ icon: UserSquare2, title: "Clientes", path: "/clients" as const }]
      : []),
    ...(hasPerm(perms, su, "manage_services")
      ? [{ icon: Drill, title: "Serviços", path: "/services" as const }]
      : []),
    ...(hasPerm(perms, su, "view_financeiro")
      ? [
          {
            icon: Wallet,
            title: "Financeiro",
            path: "/financeiro" as const,
          },
        ]
      : []),
    ...(hasPerm(perms, su, "view_financeiro")
      ? [
          {
            icon: LayoutDashboard,
            title: "Transações",
            path: "/financeiro/transacoes" as const,
          },
        ]
      : []),
    ...(hasPerm(perms, su, "view_contas_pagar")
      ? [
          {
            icon: ArrowDownCircle,
            title: "Despesas",
            path: "/financeiro/contas-a-pagar" as const,
          },
        ]
      : []),
    ...(hasPerm(perms, su, "view_contas_receber")
      ? [
          {
            icon: ArrowUpCircle,
            title: "Receitas",
            path: "/financeiro/contas-a-receber" as const,
          },
        ]
      : []),
    ...(hasPerm(perms, su, "view_fornecedores")
      ? [
          {
            icon: Truck,
            title: "Fornecedores",
            path: "/fornecedores" as const,
          },
        ]
      : []),
    ...(hasPerm(perms, su, "manage_users")
      ? [{ icon: Users, title: "Usuários", path: "/admin" as const }]
      : []),
    ...(hasPerm(perms, su, "manage_permissions")
      ? [{ icon: Lock, title: "Permissões", path: "/permissions" as const }]
      : []),
  ]

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
