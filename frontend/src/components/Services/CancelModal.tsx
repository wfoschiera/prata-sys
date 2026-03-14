import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { ServicesService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CancelModalProps {
  serviceId: string
  isOpen: boolean
  onClose: () => void
}

const CancelModal = ({ serviceId, isOpen, onClose }: CancelModalProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [reason, setReason] = useState("")

  const mutation = useMutation({
    mutationFn: () =>
      ServicesService.transitionService({
        serviceId,
        requestBody: { to_status: "cancelled", reason },
      }),
    onSuccess: () => {
      showSuccessToast("Serviço cancelado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["services"] })
      queryClient.invalidateQueries({ queryKey: ["services", serviceId] })
      setReason("")
      onClose()
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const handleClose = () => {
    if (!mutation.isPending) {
      setReason("")
      onClose()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cancelar Serviço</DialogTitle>
          <DialogDescription>
            Informe o motivo do cancelamento. Esta ação não pode ser desfeita.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="cancel-reason">Motivo *</Label>
          <Textarea
            id="cancel-reason"
            placeholder="Descreva o motivo do cancelamento..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            disabled={mutation.isPending}
          />
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={mutation.isPending}
          >
            Voltar
          </Button>
          <LoadingButton
            variant="destructive"
            onClick={() => mutation.mutate()}
            disabled={reason.trim().length === 0}
            loading={mutation.isPending}
          >
            Confirmar Cancelamento
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default CancelModal
