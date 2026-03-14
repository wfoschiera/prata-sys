import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { Pencil, Plus, Trash2 } from "lucide-react"
import { Suspense, useState } from "react"

import { type ClientPublic, ClientsService, UsersService } from "@/client"
import ClientForm from "@/components/Clients/ClientForm"
import DeleteClient from "@/components/Clients/DeleteClient"
import { Button } from "@/components/ui/button"
import { PaginationBar } from "@/components/ui/pagination-bar"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const PAGE_SIZE = 20

function getClientsQueryOptions(page: number) {
  return {
    queryFn: () =>
      ClientsService.readClients({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
    queryKey: ["clients", page],
  }
}

export const Route = createFileRoute("/_layout/clients")({
  component: Clients,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    // Block users with role=client; admin and finance are allowed
    if ((user as any).role === "client") {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Clientes - Prata Sys",
      },
    ],
  }),
})

function ClientsTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

interface ClientsTableContentProps {
  page: number
  onEdit: (client: ClientPublic) => void
  onDelete: (client: ClientPublic) => void
  onPageChange: (page: number) => void
}

function ClientsTableContent({
  page,
  onEdit,
  onDelete,
  onPageChange,
}: ClientsTableContentProps) {
  const { data: clients } = useSuspenseQuery(getClientsQueryOptions(page))

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Documento</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Telefone</TableHead>
            <TableHead>
              <span className="sr-only">Ações</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clients.data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-center text-muted-foreground py-8"
              >
                Nenhum cliente cadastrado.
              </TableCell>
            </TableRow>
          ) : (
            clients.data.map((client) => (
              <TableRow key={client.id}>
                <TableCell className="font-medium">{client.name}</TableCell>
                <TableCell className="uppercase text-xs">
                  {client.document_type}
                </TableCell>
                <TableCell className="font-mono">
                  {client.document_number}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {client.email ?? "—"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {client.phone ?? "—"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onEdit(client)}
                      aria-label="Editar cliente"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => onDelete(client)}
                      aria-label="Excluir cliente"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <PaginationBar
        page={page}
        pageSize={PAGE_SIZE}
        total={clients.count}
        onPageChange={onPageChange}
      />
    </>
  )
}

function Clients() {
  const [page, setPage] = useState(1)
  const [formOpen, setFormOpen] = useState(false)
  const [editClient, setEditClient] = useState<ClientPublic | null>(null)
  const [deleteClient, setDeleteClient] = useState<ClientPublic | null>(null)

  const handleEdit = (client: ClientPublic) => {
    setEditClient(client)
    setFormOpen(true)
  }

  const handleFormClose = () => {
    setFormOpen(false)
    setEditClient(null)
  }

  const handleDeleteClose = () => {
    setDeleteClient(null)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Clientes</h1>
          <p className="text-muted-foreground">
            Gerencie os clientes cadastrados no sistema
          </p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Adicionar Cliente
        </Button>
      </div>

      <Suspense fallback={<ClientsTableSkeleton />}>
        <ClientsTableContent
          page={page}
          onEdit={handleEdit}
          onDelete={setDeleteClient}
          onPageChange={setPage}
        />
      </Suspense>

      <ClientForm
        isOpen={formOpen}
        onClose={handleFormClose}
        client={editClient ?? undefined}
      />

      {deleteClient && (
        <DeleteClient
          id={deleteClient.id}
          name={deleteClient.name}
          isOpen={!!deleteClient}
          onClose={handleDeleteClose}
        />
      )}
    </div>
  )
}
