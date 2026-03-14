import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { type ServiceItemRead, ServicesService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CompleteConfirmModalProps {
  serviceId: string
  materialItems: ServiceItemRead[]
  isOpen: boolean
  onClose: () => void
}

const CompleteConfirmModal = ({
  serviceId,
  materialItems,
  isOpen,
  onClose,
}: CompleteConfirmModalProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const [quantities, setQuantities] = useState<Record<string, number>>(() =>
    Object.fromEntries(materialItems.map((item) => [item.id, item.quantity])),
  )

  const allValid = Object.values(quantities).every((q) => q > 0)

  const mutation = useMutation({
    mutationFn: () =>
      ServicesService.transitionService({
        serviceId,
        requestBody: {
          to_status: "completed",
          deduction_items: Object.entries(quantities).map(([id, qty]) => ({
            service_item_id: id,
            quantity: qty,
          })),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Serviço concluído com sucesso")
      queryClient.invalidateQueries({ queryKey: ["services"] })
      queryClient.invalidateQueries({ queryKey: ["services", serviceId] })
      onClose()
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => !open && !mutation.isPending && onClose()}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Concluir Serviço</DialogTitle>
          <DialogDescription>
            Confirme as quantidades de materiais a baixar do estoque.
          </DialogDescription>
        </DialogHeader>

        {materialItems.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nenhum item de material cadastrado para este serviço.
          </p>
        ) : (
          <div className="space-y-3">
            {materialItems.map((item) => (
              <div key={item.id} className="flex items-center gap-3">
                <Label className="flex-1 text-sm">{item.description}</Label>
                <Input
                  type="number"
                  min={0.01}
                  step={0.01}
                  value={quantities[item.id] ?? item.quantity}
                  onChange={(e) =>
                    setQuantities((prev) => ({
                      ...prev,
                      [item.id]: e.target.valueAsNumber,
                    }))
                  }
                  className="w-24 text-right"
                  disabled={mutation.isPending}
                />
              </div>
            ))}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={mutation.isPending}
          >
            Cancelar
          </Button>
          <LoadingButton
            onClick={() => mutation.mutate()}
            disabled={!allValid}
            loading={mutation.isPending}
          >
            Confirmar Conclusão
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default CompleteConfirmModal
