import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { useCallback, useMemo } from "react"
import type { UserPermissionsOut } from "@/client"
import { PermissionsService, UsersService } from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/permissions")({
  component: PermissionsPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("manage_permissions")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Permissões - Prata Sys" }],
  }),
})

const permGroupLabels: Record<string, string> = {
  manage: "Gestão",
  view: "Visualização",
}

function groupPermissions(
  perms: Record<string, string>,
): { group: string; items: [string, string][] }[] {
  const groups: Record<string, [string, string][]> = {}
  for (const [key, label] of Object.entries(perms)) {
    const prefix = key.split("_")[0]
    const group = permGroupLabels[prefix] ?? prefix
    if (!groups[group]) groups[group] = []
    groups[group].push([key, label])
  }
  return Object.entries(groups).map(([group, items]) => ({ group, items }))
}

function PermissionsPage() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: available } = useQuery({
    queryKey: ["permissions", "available"],
    queryFn: () => PermissionsService.getAvailablePermissions(),
  })

  const { data: users } = useQuery({
    queryKey: ["permissions", "users"],
    queryFn: () => PermissionsService.getUsersPermissions(),
  })

  const mutation = useMutation({
    mutationFn: ({
      userId,
      permissions,
    }: {
      userId: string
      permissions: string[]
    }) =>
      PermissionsService.setUserPermissions({
        userId,
        requestBody: { permissions },
      }),
    onSuccess: () => {
      showSuccessToast("Permissões atualizadas")
      queryClient.invalidateQueries({ queryKey: ["permissions", "users"] })
    },
    onError: () => showErrorToast("Erro ao atualizar permissões"),
  })

  const groups = useMemo(
    () => (available ? groupPermissions(available) : []),
    [available],
  )

  const allPermKeys = useMemo(
    () => groups.flatMap((g) => g.items.map(([k]) => k)),
    [groups],
  )

  const togglePermission = useCallback(
    (user: UserPermissionsOut, perm: string) => {
      const currentOverrides = new Set(user.overrides)
      if (currentOverrides.has(perm)) {
        currentOverrides.delete(perm)
      } else {
        currentOverrides.add(perm)
      }
      mutation.mutate({
        userId: user.id,
        permissions: [...currentOverrides],
      })
    },
    [mutation],
  )

  if (!available || !users) {
    return <div className="p-6">Carregando...</div>
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Permissões</h1>
        <p className="text-muted-foreground">
          Gerencie as permissões de acesso dos usuários
        </p>
      </div>

      <TooltipProvider>
        <div className="rounded-md border overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 bg-background z-10 min-w-[200px]">
                  Usuário
                </TableHead>
                {groups.map((g) =>
                  g.items.map(([key, label]) => (
                    <TableHead
                      key={key}
                      className="text-center text-xs min-w-[100px]"
                    >
                      <div>{label}</div>
                    </TableHead>
                  )),
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="sticky left-0 bg-background z-10">
                    <div className="font-medium">
                      {user.full_name || user.email}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {user.role}
                      {user.is_superuser && " · superusuário"}
                    </div>
                  </TableCell>
                  {allPermKeys.map((perm) => {
                    const isRoleDefault = user.role_defaults.includes(perm)
                    const isOverride = user.overrides.includes(perm)
                    const isEffective = user.effective.includes(perm)

                    if (user.is_superuser) {
                      return (
                        <TableCell key={perm} className="text-center">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div className="flex justify-center">
                                <Checkbox checked disabled />
                              </div>
                            </TooltipTrigger>
                            <TooltipContent>
                              Acesso total (superusuário)
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                      )
                    }

                    if (isRoleDefault) {
                      return (
                        <TableCell key={perm} className="text-center">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div className="flex justify-center">
                                <Checkbox checked disabled />
                              </div>
                            </TooltipTrigger>
                            <TooltipContent>
                              Padrão do perfil {user.role}
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                      )
                    }

                    return (
                      <TableCell key={perm} className="text-center">
                        <div className="flex justify-center">
                          <Checkbox
                            checked={isOverride || isEffective}
                            onCheckedChange={() => togglePermission(user, perm)}
                            disabled={mutation.isPending}
                          />
                        </div>
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </TooltipProvider>
    </div>
  )
}
