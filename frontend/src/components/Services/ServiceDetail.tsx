import { useQuery } from "@tanstack/react-query"

import { type ServiceStatus, ServicesService } from "@/client"
import { Badge } from "@/components/ui/badge"
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

const STATUS_LABELS: Record<ServiceStatus, string> = {
  requested: "Solicitado",
  scheduled: "Agendado",
  executing: "Em Execução",
  completed: "Concluído",
}

const STATUS_VARIANTS: Record<
  ServiceStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  requested: "secondary",
  scheduled: "outline",
  executing: "default",
  completed: "secondary",
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
  const { data: service } = useQuery({
    queryKey: ["services", serviceId],
    queryFn: () => ServicesService.readService({ serviceId: serviceId! }),
    enabled: !!serviceId,
  })

  const grandTotal =
    (service?.items ?? []).reduce(
      (sum, item) => sum + item.quantity * item.unit_price,
      0,
    ) ?? 0

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
