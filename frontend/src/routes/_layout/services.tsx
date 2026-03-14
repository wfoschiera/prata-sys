import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Eye, Plus, Trash2 } from "lucide-react"
import { Suspense, useState } from "react"

import {
  type ServiceListRead,
  type ServiceStatus,
  ServicesService,
} from "@/client"
import DeleteService from "@/components/Services/DeleteService"
import ServiceDetail from "@/components/Services/ServiceDetail"
import ServiceForm from "@/components/Services/ServiceForm"
import StockWarningBadge from "@/components/Services/StockWarningBadge"
import { Badge } from "@/components/ui/badge"
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

const STATUS_LABELS: Record<ServiceStatus, string> = {
  requested: "Solicitado",
  scheduled: "Agendado",
  executing: "Em Execução",
  completed: "Concluído",
  cancelled: "Cancelado",
}

const STATUS_VARIANTS: Record<
  ServiceStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  requested: "secondary",
  scheduled: "outline",
  executing: "default",
  completed: "secondary",
  cancelled: "destructive",
}

const TYPE_LABELS: Record<string, string> = {
  perfuração: "Perfuração",
  reparo: "Reparo",
}

const PAGE_SIZE = 20

function getServicesQueryOptions(page: number) {
  return {
    queryFn: () =>
      ServicesService.readServices({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
    queryKey: ["services", page],
  }
}

export const Route = createFileRoute("/_layout/services")({
  component: Services,
  head: () => ({
    meta: [
      {
        title: "Serviços - Prata Sys",
      },
    ],
  }),
})

function ServicesTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

interface ServicesTableContentProps {
  page: number
  onView: (service: ServiceListRead) => void
  onDelete: (service: ServiceListRead) => void
  onPageChange: (page: number) => void
}

function ServicesTableContent({
  page,
  onView,
  onDelete,
  onPageChange,
}: ServicesTableContentProps) {
  const { data: services } = useSuspenseQuery(getServicesQueryOptions(page))

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Cliente</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Endereço de Execução</TableHead>
            <TableHead>
              <span className="sr-only">Ações</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {services.data.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="text-center text-muted-foreground py-8"
              >
                Nenhum serviço cadastrado.
              </TableCell>
            </TableRow>
          ) : (
            services.data.map((service) => (
              <TableRow key={service.id}>
                <TableCell className="font-medium">
                  {service.client?.name ?? "—"}
                </TableCell>
                <TableCell>
                  {TYPE_LABELS[service.type] ?? service.type}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    <Badge variant={STATUS_VARIANTS[service.status]}>
                      {STATUS_LABELS[service.status] ?? service.status}
                    </Badge>
                    {service.status === "scheduled" && (
                      <StockWarningBadge
                        hasStockWarning={service.has_stock_warning ?? false}
                        compact
                      />
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground max-w-xs truncate">
                  {service.execution_address}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onView(service)}
                      aria-label="Ver detalhes"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => onDelete(service)}
                      aria-label="Excluir serviço"
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
        total={services.count}
        onPageChange={onPageChange}
      />
    </>
  )
}

function Services() {
  const [page, setPage] = useState(1)
  const [formOpen, setFormOpen] = useState(false)
  const [detailServiceId, setDetailServiceId] = useState<string | null>(null)
  const [deleteService, setDeleteService] = useState<ServiceListRead | null>(
    null,
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Serviços</h1>
          <p className="text-muted-foreground">
            Gerencie os serviços cadastrados no sistema
          </p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Serviço
        </Button>
      </div>

      <Suspense fallback={<ServicesTableSkeleton />}>
        <ServicesTableContent
          page={page}
          onView={(s) => setDetailServiceId(s.id)}
          onDelete={setDeleteService}
          onPageChange={setPage}
        />
      </Suspense>

      <ServiceForm isOpen={formOpen} onClose={() => setFormOpen(false)} />

      <ServiceDetail
        serviceId={detailServiceId}
        onClose={() => setDetailServiceId(null)}
      />

      {deleteService && (
        <DeleteService
          id={deleteService.id}
          isOpen={!!deleteService}
          onClose={() => setDeleteService(null)}
        />
      )}
    </div>
  )
}
