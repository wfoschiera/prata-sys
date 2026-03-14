import type { ServiceStatus } from "@/client"

const ORDERED_STEPS: ServiceStatus[] = [
  "requested",
  "scheduled",
  "executing",
  "completed",
]

const STEP_LABELS: Record<ServiceStatus, string> = {
  requested: "Solicitado",
  scheduled: "Agendado",
  executing: "Em Execução",
  completed: "Concluído",
  cancelled: "Cancelado",
}

interface StatusTimelineProps {
  currentStatus: ServiceStatus
  cancelledReason?: string | null
}

const StatusTimeline = ({
  currentStatus,
  cancelledReason,
}: StatusTimelineProps) => {
  const isCancelled = currentStatus === "cancelled"
  const currentIndex = isCancelled
    ? ORDERED_STEPS.length
    : ORDERED_STEPS.indexOf(currentStatus)

  return (
    <div className="space-y-2">
      <ol className="flex items-center gap-0">
        {ORDERED_STEPS.map((step, idx) => {
          const done = !isCancelled && idx <= currentIndex
          const active = !isCancelled && idx === currentIndex
          return (
            <li key={step} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors
                    ${done ? "bg-primary border-primary text-primary-foreground" : "bg-muted border-muted-foreground/30 text-muted-foreground"}
                    ${active ? "ring-2 ring-primary ring-offset-2" : ""}
                  `}
                >
                  {idx + 1}
                </div>
                <span
                  className={`text-xs mt-1 text-center leading-tight ${done ? "text-primary font-medium" : "text-muted-foreground"}`}
                >
                  {STEP_LABELS[step]}
                </span>
              </div>
              {idx < ORDERED_STEPS.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-1 mb-4 ${idx < currentIndex ? "bg-primary" : "bg-muted-foreground/20"}`}
                />
              )}
            </li>
          )
        })}

        {isCancelled && (
          <li className="flex items-center">
            <div className="h-0.5 w-6 mx-1 mb-4 bg-destructive/40" />
            <div className="flex flex-col items-center">
              <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 bg-destructive border-destructive text-destructive-foreground">
                ✕
              </div>
              <span className="text-xs mt-1 text-center leading-tight text-destructive font-medium">
                Cancelado
              </span>
            </div>
          </li>
        )}
      </ol>

      {isCancelled && cancelledReason && (
        <p className="text-xs text-destructive bg-destructive/10 rounded px-3 py-2 mt-1">
          <span className="font-semibold">Motivo:</span> {cancelledReason}
        </p>
      )}
    </div>
  )
}

export default StatusTimeline
