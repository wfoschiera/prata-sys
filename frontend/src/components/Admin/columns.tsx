import type { ColumnDef } from "@tanstack/react-table"
import { ShieldCheck } from "lucide-react"

import type { UserPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

const roleBadgeVariant: Record<string, "default" | "secondary" | "outline"> = {
  admin: "default",
  finance: "secondary",
  client: "outline",
}

const roleLabel: Record<string, string> = {
  admin: "Administrador",
  finance: "Financeiro",
  client: "Cliente",
}

export type UserTableData = UserPublic & {
  isCurrentUser: boolean
}

export const columns: ColumnDef<UserTableData>[] = [
  {
    accessorKey: "full_name",
    header: "Full Name",
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || "N/A"}
          </span>
          {row.original.isCurrentUser && (
            <Badge variant="outline" className="text-xs">
              You
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email}</span>
    ),
  },
  {
    accessorKey: "role",
    header: "Perfil",
    cell: ({ row }) => {
      const role = row.original.role ?? "admin"
      return (
        <div className="flex items-center gap-1.5">
          <Badge variant={roleBadgeVariant[role] ?? "outline"}>
            {roleLabel[role] ?? role}
          </Badge>
          {row.original.is_superuser && (
            <ShieldCheck
              className="size-4 text-amber-500"
              aria-label="Superuser"
              title="Superuser"
            />
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "size-2 rounded-full",
            row.original.is_active ? "bg-green-500" : "bg-gray-400",
          )}
        />
        <span className={row.original.is_active ? "" : "text-muted-foreground"}>
          {row.original.is_active ? "Active" : "Inactive"}
        </span>
      </div>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <UserActionsMenu user={row.original} />
      </div>
    ),
  },
]
