import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { type ServiceStatus, ServicesService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import StatusTimeline from "./StatusTimeline"
import StockWarningBadge from "./StockWarningBadge"
import TransitionButtons from "./TransitionButtons"

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

interface ServiceDetailProps {
  serviceId: string | null
  onClose: () => void
}

const ServiceDetail = ({ serviceId, onClose }: ServiceDetailProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()
  const isAdmin = !!user?.is_superuser || user?.role === "admin"

  const { data: service } = useQuery({
    queryKey: ["services", serviceId],
    queryFn: () => ServicesService.readService({ serviceId: serviceId! }),
    enabled: !!serviceId,
  })

  const deductMutation = useMutation({
    mutationFn: () => ServicesService.deductStock({ serviceId: serviceId! }),
    onSuccess: () => {
      showSuccessToast("Materiais baixados do estoque com sucesso")
      queryClient.invalidateQueries({ queryKey: ["services"] })
      queryClient.invalidateQueries({ queryKey: ["services", serviceId] })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const grandTotal =
    (service?.items ?? []).reduce(
      (sum, item) => sum + item.quantity * item.unit_price,
      0,
    ) ?? 0

  const materialItems = (service?.items ?? []).filter(
    (item) => item.item_type === "material",
  )

  return (
    <Sheet open={!!serviceId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="sm:max-w-xl overflow-y-auto">
        {service ? (
          <>
            <SheetHeader className="mb-4">
              <SheetTitle className="flex items-center gap-2">
                {TYPE_LABELS[service.type] ?? service.type}
                <Badge variant={STATUS_VARIANTS[service.status]}>
                  {STATUS_LABELS[service.status] ?? service.status}
                </Badge>
              </SheetTitle>
              <SheetDescription>{service.client?.name ?? "—"}</SheetDescription>
            </SheetHeader>

            <div className="space-y-4">
              <StatusTimeline
                currentStatus={service.status}
                cancelledReason={service.cancelled_reason}
              />

              {service.status === "scheduled" && service.has_stock_warning && (
                <StockWarningBadge hasStockWarning />
              )}

              <TransitionButtons
                serviceId={service.id}
                currentStatus={service.status}
                isAdmin={isAdmin}
                materialItems={materialItems}
              />

              {isAdmin && service.status === "executing" && (
                <LoadingButton
                  variant="outline"
                  onClick={() => deductMutation.mutate()}
                  loading={deductMutation.isPending}
                >
                  Baixar do Estoque
                </LoadingButton>
              )}

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                  Endereço de Execução
                </p>
                <p className="text-sm">{service.execution_address}</p>
              </div>

              {service.notes && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                    Observações
                  </p>
                  <p className="text-sm whitespace-pre-wrap">{service.notes}</p>
                </div>
              )}

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Itens
                </p>
                {(service.items ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Nenhum item cadastrado.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Descrição</TableHead>
                        <TableHead className="text-right">Qtd</TableHead>
                        <TableHead className="text-right">
                          Preço Unit.
                        </TableHead>
                        <TableHead className="text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(service.items ?? []).map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <span className="font-medium text-xs uppercase text-muted-foreground mr-1">
                              [{item.item_type}]
                            </span>
                            {item.description}
                          </TableCell>
                          <TableCell className="text-right">
                            {item.quantity}
                          </TableCell>
                          <TableCell className="text-right">
                            {item.unit_price.toLocaleString("pt-BR", {
                              style: "currency",
                              currency: "BRL",
                            })}
                          </TableCell>
                          <TableCell className="text-right">
                            {(item.quantity * item.unit_price).toLocaleString(
                              "pt-BR",
                              {
                                style: "currency",
                                currency: "BRL",
                              },
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                    <TableFooter>
                      <TableRow>
                        <TableCell colSpan={3} className="font-medium">
                          Total Geral
                        </TableCell>
                        <TableCell className="text-right font-bold">
                          {grandTotal.toLocaleString("pt-BR", {
                            style: "currency",
                            currency: "BRL",
                          })}
                        </TableCell>
                      </TableRow>
                    </TableFooter>
                  </Table>
                )}
              </div>
            </div>
          </>
        ) : (
          <SheetHeader>
            <SheetTitle>Carregando...</SheetTitle>
          </SheetHeader>
        )}
      </SheetContent>
    </Sheet>
  )
}

export default ServiceDetail
