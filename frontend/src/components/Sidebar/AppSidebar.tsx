import { Home, Users, UserSquare2 } from "lucide-react"

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

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const role = (currentUser as any)?.role
  const isAdminOrFinance = currentUser?.is_superuser || role === "admin" || role === "finance"

  const items = [
    ...baseItems,
    ...(isAdminOrFinance
      ? [{ icon: UserSquare2, title: "Clientes", path: "/clients" }]
      : []),
    ...(currentUser?.is_superuser
      ? [{ icon: Users, title: "Admin", path: "/admin" }]
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
