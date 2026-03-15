import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createFileRoute,
  Link,
  redirect,
  useNavigate,
} from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { useState } from "react"

import {
  ClientsService,
  type OrcamentoCreate,
  OrcamentosService,
  UsersService,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/orcamentos/new")({
  component: NewOrcamento,
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
    meta: [{ title: "Novo Orçamento - Prata Sys" }],
  }),
})

function NewOrcamento() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const [clientId, setClientId] = useState("")
  const [serviceType, setServiceType] = useState<"perfuração" | "reparo">(
    "perfuração",
  )
  const [executionAddress, setExecutionAddress] = useState("")
  const [city, setCity] = useState("")
  const [cep, setCep] = useState("")
  const [description, setDescription] = useState("")
  const [notes, setNotes] = useState("")
  const [formaPagamento, setFormaPagamento] = useState("")
  const [vendedor, setVendedor] = useState("")

  const { data: clients } = useQuery({
    queryKey: ["clients-all"],
    queryFn: () => ClientsService.readClients({ skip: 0, limit: 500 }),
  })

  const createMutation = useMutation({
    mutationFn: (body: OrcamentoCreate) =>
      OrcamentosService.createOrcamento({ requestBody: body }),
    onSuccess: (data) => {
      showSuccessToast("Orçamento criado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["orcamentos"] })
      void navigate({
        to: "/orcamentos/$orcamentoId",
        params: { orcamentoId: data.id },
      })
    },
    onError: (err: unknown) => {
      handleError.call(showErrorToast, err)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      client_id: clientId,
      service_type: serviceType,
      execution_address: executionAddress,
      city: city || undefined,
      cep: cep || undefined,
      description: description || undefined,
      notes: notes || undefined,
      forma_pagamento: formaPagamento || undefined,
      vendedor: vendedor || undefined,
    })
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/orcamentos">
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            Voltar
          </Link>
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">Novo Orçamento</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="client">Cliente *</Label>
            <Select value={clientId} onValueChange={setClientId}>
              <SelectTrigger id="client">
                <SelectValue placeholder="Selecione o cliente" />
              </SelectTrigger>
              <SelectContent>
                {(clients?.data ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} ({c.document_number})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="type">Tipo de Serviço *</Label>
            <Select
              value={serviceType}
              onValueChange={(v) =>
                setServiceType(v as "perfuração" | "reparo")
              }
            >
              <SelectTrigger id="type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="perfuração">Perfuração</SelectItem>
                <SelectItem value="reparo">Reparo</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Endereço de Execução *</Label>
          <Input
            id="address"
            value={executionAddress}
            onChange={(e) => setExecutionAddress(e.target.value)}
            placeholder="Rua, número, complemento"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="city">Cidade</Label>
            <Input
              id="city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Cidade - UF"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cep">CEP</Label>
            <Input
              id="cep"
              value={cep}
              onChange={(e) => setCep(e.target.value)}
              placeholder="00000-000"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Descrição resumida</Label>
          <Input
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Ex: Perfuração de poço artesiano - Fazenda São João"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Observações</Label>
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notas adicionais..."
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="pagamento">Forma de pagamento</Label>
            <Input
              id="pagamento"
              value={formaPagamento}
              onChange={(e) => setFormaPagamento(e.target.value)}
              placeholder="À vista, 2x, etc."
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="vendedor">Vendedor</Label>
            <Input
              id="vendedor"
              value={vendedor}
              onChange={(e) => setVendedor(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="outline" asChild>
            <Link to="/orcamentos">Cancelar</Link>
          </Button>
          <LoadingButton
            type="submit"
            isLoading={createMutation.isPending}
            disabled={!clientId || !executionAddress}
          >
            Criar Orçamento
          </LoadingButton>
        </div>
      </form>
    </div>
  )
}
