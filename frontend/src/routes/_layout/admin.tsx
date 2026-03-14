import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Suspense, useState } from "react"

import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import { PaginationBar } from "@/components/ui/pagination-bar"
import useAuth from "@/hooks/useAuth"

const PAGE_SIZE = 20

function getUsersQueryOptions(page: number) {
  return {
    queryFn: () =>
      UsersService.readUsers({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
    queryKey: ["users", page],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser && !user.permissions?.includes("manage_users")) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Admin - FastAPI Template",
      },
    ],
  }),
})

interface UsersTableContentProps {
  page: number
  onPageChange: (page: number) => void
}

function UsersTableContent({ page, onPageChange }: UsersTableContentProps) {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions(page))

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return (
    <>
      <DataTable columns={columns} data={tableData} />
      <PaginationBar
        page={page}
        pageSize={PAGE_SIZE}
        total={users.count}
        onPageChange={onPageChange}
      />
    </>
  )
}

function UsersTable({ page, onPageChange }: UsersTableContentProps) {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent page={page} onPageChange={onPageChange} />
    </Suspense>
  )
}

function Admin() {
  const [page, setPage] = useState(1)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Usuários</h1>
          <p className="text-muted-foreground">
            Gerencie as contas de usuário e permissões
          </p>
        </div>
        <AddUser />
      </div>
      <UsersTable page={page} onPageChange={setPage} />
    </div>
  )
}
