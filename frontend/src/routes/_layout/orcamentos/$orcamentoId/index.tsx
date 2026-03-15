import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import {
  type OrcamentoStatus,
  OrcamentosService,
  SettingsService,
  UsersService,
} from "@/client"
import OrcamentoDetail from "@/components/Orcamentos/OrcamentoDetail"
import { Skeleton } from "@/components/ui/skeleton"
import "@/components/Orcamentos/orcamento-print.css"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/orcamentos/$orcamentoId/")({
  component: OrcamentoDetailPage,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("manage_orcamentos")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Orçamento - Prata Sys" }],
  }),
})

function OrcamentoDetailPage() {
  const { orcamentoId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: orcamento, isLoading: orcLoading } = useQuery({
    queryKey: ["orcamentos", orcamentoId],
    queryFn: () => OrcamentosService.readOrcamento({ orcamentoId }),
  })

  const { data: company, isLoading: companyLoading } = useQuery({
    queryKey: ["company-settings"],
    queryFn: () => SettingsService.getCompanySettings(),
  })

  const transitionMutation = useMutation({
    mutationFn: (params: { toStatus: OrcamentoStatus; reason?: string }) =>
      OrcamentosService.transitionOrcamento({
        orcamentoId,
        requestBody: {
          to_status: params.toStatus,
          reason: params.reason,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Status atualizado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] })
    },
    onError: (err: unknown) => {
      handleError.call(showErrorToast, err as any)
    },
  })

  const convertMutation = useMutation({
    mutationFn: () => OrcamentosService.convertToService({ orcamentoId }),
    onSuccess: (_data) => {
      showSuccessToast("Serviço criado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] })
      void navigate({ to: "/services" })
    },
    onError: (err: unknown) => {
      handleError.call(showErrorToast, err as any)
    },
  })

  const duplicateMutation = useMutation({
    mutationFn: () => OrcamentosService.duplicateOrcamento({ orcamentoId }),
    onSuccess: (data) => {
      showSuccessToast("Orçamento duplicado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] })
      void navigate({
        to: "/orcamentos/$orcamentoId",
        params: { orcamentoId: data.id },
      })
    },
    onError: (err: unknown) => {
      handleError.call(showErrorToast, err as any)
    },
  })

  if (orcLoading || companyLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!orcamento || !company) {
    return (
      <div className="max-w-4xl mx-auto py-8 text-center text-muted-foreground">
        Orçamento não encontrado.
      </div>
    )
  }

  return (
    <OrcamentoDetail
      orcamento={orcamento as any}
      company={company as any}
      onTransition={(toStatus, reason) =>
        transitionMutation.mutate({
          toStatus: toStatus as OrcamentoStatus,
          reason,
        })
      }
      onConvertToService={() => convertMutation.mutate()}
      onDuplicate={() => duplicateMutation.mutate()}
      isTransitioning={transitionMutation.isPending}
      isConverting={convertMutation.isPending}
      isDuplicating={duplicateMutation.isPending}
    />
  )
}
