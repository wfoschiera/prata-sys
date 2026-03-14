import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { ServiceItemRead } from "@/client"
import { type ServiceStatus, ServicesService } from "@/client"
import { Button } from "@/components/ui/button"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import CancelModal from "./CancelModal"
import CompleteConfirmModal from "./CompleteConfirmModal"

const VALID_TRANSITIONS: Record<ServiceStatus, ServiceStatus[]> = {
  requested: ["scheduled", "cancelled"],
  scheduled: ["executing", "cancelled"],
  executing: ["completed", "cancelled"],
  completed: [],
  cancelled: [],
}

const NEXT_STATUS_LABELS: Partial<Record<ServiceStatus, string>> = {
  scheduled: "Agendar",
  executing: "Iniciar Execução",
  completed: "Concluir",
}

interface TransitionButtonsProps {
  serviceId: string
  currentStatus: ServiceStatus
  isAdmin: boolean
  materialItems: ServiceItemRead[]
}

const TransitionButtons = ({
  serviceId,
  currentStatus,
  isAdmin,
  materialItems,
}: TransitionButtonsProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [cancelOpen, setCancelOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)

  const forwardTransitions = VALID_TRANSITIONS[currentStatus].filter(
    (s) => s !== "cancelled",
  )
  const canCancel = VALID_TRANSITIONS[currentStatus].includes("cancelled")

  const forwardMutation = useMutation({
    mutationFn: (toStatus: ServiceStatus) =>
      ServicesService.transitionService({
        serviceId,
        requestBody: { to_status: toStatus },
      }),
    onSuccess: () => {
      showSuccessToast("Status atualizado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["services"] })
      queryClient.invalidateQueries({ queryKey: ["services", serviceId] })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  if (!isAdmin || (forwardTransitions.length === 0 && !canCancel)) {
    return null
  }

  return (
    <>
      <div className="flex flex-wrap gap-2">
        {forwardTransitions.map((status) =>
          status === "completed" ? (
            <Button key={status} onClick={() => setCompleteOpen(true)}>
              {NEXT_STATUS_LABELS[status] ?? status}
            </Button>
          ) : (
            <LoadingButton
              key={status}
              onClick={() => forwardMutation.mutate(status)}
              loading={
                forwardMutation.isPending &&
                forwardMutation.variables === status
              }
            >
              {NEXT_STATUS_LABELS[status] ?? status}
            </LoadingButton>
          ),
        )}
        {canCancel && (
          <Button variant="destructive" onClick={() => setCancelOpen(true)}>
            Cancelar Serviço
          </Button>
        )}
      </div>

      <CancelModal
        serviceId={serviceId}
        isOpen={cancelOpen}
        onClose={() => setCancelOpen(false)}
      />
      <CompleteConfirmModal
        serviceId={serviceId}
        materialItems={materialItems}
        isOpen={completeOpen}
        onClose={() => setCompleteOpen(false)}
      />
    </>
  )
}

export default TransitionButtons
