/**
 * Form for registering an entrada de estoque (one delivery).
 *
 * Captures the lots received with their invoice unit cost, plus the typed cost
 * adjustments that apply to the delivery as a whole. The apportionment preview
 * mirrors the backend's value-share formula so the real unit cost is visible
 * before submit.
 */
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Plus, Trash2 } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import {
  type EntradaEstoqueCreate,
  EntradasEstoqueService,
  FornecedoresService,
  ProductsService,
  type TipoCustoAjuste,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
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
import {
  AJUSTE_LABELS,
  apportionAjustes,
  custoUnitarioReal,
  isNegativeTipo,
  TIPO_AJUSTE_OPTIONS,
} from "./custoAquisicao"

const itemSchema = z.object({
  product_id: z
    .string({ error: "Produto é obrigatório" })
    .min(1, "Produto é obrigatório"),
  quantity: z
    .number({ error: "Quantidade deve ser um número" })
    .gt(0, "Quantidade deve ser > 0"),
  custo_unitario_nf: z
    .number({ error: "Custo deve ser um número" })
    .min(0, "Custo deve ser ≥ 0"),
})

const ajusteSchema = z
  .object({
    tipo: z
      .string({ error: "Tipo é obrigatório" })
      .min(1, "Tipo é obrigatório"),
    valor: z.number({ error: "Valor deve ser um número" }),
    documento_referencia: z.string().optional(),
    observacao: z.string().optional(),
  })
  .refine((a) => a.valor !== 0, {
    message: "Valor não pode ser zero",
    path: ["valor"],
  })
  .refine((a) => !isNegativeTipo(a.tipo) || a.valor < 0, {
    message: "Descontos e devoluções devem ter valor negativo",
    path: ["valor"],
  })
  .refine((a) => isNegativeTipo(a.tipo) || a.valor > 0, {
    message: "Este tipo deve ter valor positivo",
    path: ["valor"],
  })
  .refine((a) => a.tipo !== "outros" || !!a.observacao?.trim(), {
    message: "Descreva o motivo quando o tipo for 'Outros'",
    path: ["observacao"],
  })

const entradaSchema = z.object({
  data_entrada: z
    .string({ error: "Data é obrigatória" })
    .min(1, "Data é obrigatória"),
  fornecedor_id: z.string().optional(),
  numero_documento: z.string().optional(),
  observacao: z.string().optional(),
  criar_transacao: z.boolean(),
  itens: z.array(itemSchema).min(1, "Informe ao menos um item"),
  ajustes: z.array(ajusteSchema),
})

type EntradaFormData = z.infer<typeof entradaSchema>

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })

export function EntradaForm() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<EntradaFormData>({
    resolver: zodResolver(entradaSchema),
    defaultValues: {
      data_entrada: new Date().toISOString().slice(0, 10),
      fornecedor_id: undefined,
      numero_documento: "",
      observacao: "",
      criar_transacao: false,
      itens: [{ product_id: "", quantity: 0, custo_unitario_nf: 0 }],
      ajustes: [],
    },
  })

  const itens = useFieldArray({ control: form.control, name: "itens" })
  const ajustes = useFieldArray({ control: form.control, name: "ajustes" })

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => ProductsService.listProducts({}),
  })
  const { data: fornecedores } = useQuery({
    queryKey: ["fornecedores"],
    queryFn: () => FornecedoresService.listFornecedores({}),
  })

  // Live preview — mirrors the backend apportionment so the user sees the real
  // unit cost before submitting.
  const watchedItens = form.watch("itens")
  const watchedAjustes = form.watch("ajustes")
  const totalProdutos = watchedItens.reduce(
    (acc, i) => acc + (i.quantity || 0) * (i.custo_unitario_nf || 0),
    0,
  )
  const totalAjustes = watchedAjustes.reduce(
    (acc, a) => acc + (a.valor || 0),
    0,
  )
  const shares = apportionAjustes(
    watchedItens.map((i, idx) => ({
      key: String(idx),
      quantity: i.quantity || 0,
      custoUnitario: i.custo_unitario_nf || 0,
    })),
    totalAjustes,
  )

  const createMutation = useMutation({
    mutationFn: (values: EntradaFormData) => {
      const body: EntradaEstoqueCreate = {
        data_entrada: values.data_entrada,
        fornecedor_id: values.fornecedor_id || null,
        numero_documento: values.numero_documento || null,
        observacao: values.observacao || null,
        criar_transacao: values.criar_transacao,
        itens: values.itens.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          custo_unitario_nf: i.custo_unitario_nf,
        })),
        ajustes: values.ajustes.map((a) => ({
          tipo: a.tipo as TipoCustoAjuste,
          valor: a.valor,
          documento_referencia: a.documento_referencia || null,
          observacao: a.observacao || null,
        })),
      }
      return EntradasEstoqueService.createEntradaEstoque({ requestBody: body })
    },
    onSuccess: (created) => {
      showSuccessToast("Entrada registrada com sucesso")
      queryClient.invalidateQueries({ queryKey: ["entradas-estoque"] })
      queryClient.invalidateQueries({ queryKey: ["products"] })
      queryClient.invalidateQueries({ queryKey: ["estoque", "dashboard"] })
      void navigate({
        to: "/estoque/entradas/$entradaId",
        params: { entradaId: created.id },
      })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((v) => createMutation.mutate(v))}
        className="space-y-6"
      >
        {/* Header */}
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="data_entrada"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Data da Entrada *</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="numero_documento"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Número do Documento</FormLabel>
                <FormControl>
                  <Input placeholder="Nº da nota fiscal" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="fornecedor_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fornecedor</FormLabel>
              <Select
                onValueChange={(v) =>
                  field.onChange(v === "none" ? undefined : v)
                }
                value={field.value ?? "none"}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o fornecedor" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="none">Nenhum</SelectItem>
                  {(fornecedores ?? []).map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.company_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Lots */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Itens recebidos</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                itens.append({
                  product_id: "",
                  quantity: 0,
                  custo_unitario_nf: 0,
                })
              }
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Adicionar item
            </Button>
          </div>

          {itens.fields.map((row, index) => {
            const item = watchedItens[index]
            const real = custoUnitarioReal(
              item?.quantity || 0,
              item?.custo_unitario_nf || 0,
              shares[String(index)] ?? 0,
            )
            return (
              <div
                key={row.id}
                className="grid grid-cols-12 gap-2 items-start rounded-md border p-3"
              >
                <div className="col-span-5">
                  <FormField
                    control={form.control}
                    name={`itens.${index}.product_id`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Produto *</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {(products ?? []).map((p) => (
                              <SelectItem key={p.id} value={p.id}>
                                {p.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="col-span-2">
                  <FormField
                    control={form.control}
                    name={`itens.${index}.quantity`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Qtd *</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.0001"
                            min="0"
                            value={field.value}
                            onChange={(e) =>
                              field.onChange(e.target.valueAsNumber)
                            }
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="col-span-2">
                  <FormField
                    control={form.control}
                    name={`itens.${index}.custo_unitario_nf`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Custo NF *</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.0001"
                            min="0"
                            value={field.value}
                            onChange={(e) =>
                              field.onChange(e.target.valueAsNumber)
                            }
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="col-span-2 pt-8 text-sm">
                  <span className="text-muted-foreground">Custo real: </span>
                  <span className="font-medium">{brl(real)}</span>
                </div>
                <div className="col-span-1 pt-8 flex justify-end">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    disabled={itens.fields.length === 1}
                    onClick={() => itens.remove(index)}
                    aria-label="Remover item"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )
          })}
        </div>

        {/* Adjustments */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Ajustes de custo</h2>
              <p className="text-sm text-muted-foreground">
                Cada diferença entre o valor da nota e o custo real precisa de
                um tipo e, sempre que possível, do documento que a comprova.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                ajustes.append({
                  tipo: "frete",
                  valor: 0,
                  documento_referencia: "",
                  observacao: "",
                })
              }
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Adicionar ajuste
            </Button>
          </div>

          {ajustes.fields.map((row, index) => (
            <div
              key={row.id}
              className="grid grid-cols-12 gap-2 items-start rounded-md border p-3"
            >
              <div className="col-span-3">
                <FormField
                  control={form.control}
                  name={`ajustes.${index}.tipo`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tipo *</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {TIPO_AJUSTE_OPTIONS.map((t) => (
                            <SelectItem key={t} value={t}>
                              {AJUSTE_LABELS[t]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="col-span-2">
                <FormField
                  control={form.control}
                  name={`ajustes.${index}.valor`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Valor *</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          value={field.value}
                          onChange={(e) =>
                            field.onChange(e.target.valueAsNumber)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="col-span-3">
                <FormField
                  control={form.control}
                  name={`ajustes.${index}.documento_referencia`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Documento</FormLabel>
                      <FormControl>
                        <Input placeholder="CT-e, CC-e..." {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="col-span-3">
                <FormField
                  control={form.control}
                  name={`ajustes.${index}.observacao`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Observação</FormLabel>
                      <FormControl>
                        <Input placeholder="Motivo" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="col-span-1 pt-8 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => ajustes.remove(index)}
                  aria-label="Remover ajuste"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <FormField
          control={form.control}
          name="observacao"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Observações da entrada</FormLabel>
              <FormControl>
                <Textarea rows={2} className="resize-none" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Totals + booking */}
        <div className="rounded-md border p-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total dos produtos</span>
            <span>{brl(totalProdutos)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total de ajustes</span>
            <span>{brl(totalAjustes)}</span>
          </div>
          <div className="flex justify-between font-semibold border-t pt-2">
            <span>Total real</span>
            <span>{brl(totalProdutos + totalAjustes)}</span>
          </div>
        </div>

        <FormField
          control={form.control}
          name="criar_transacao"
          render={({ field }) => (
            <FormItem className="flex flex-row items-start gap-3 rounded-md border p-4">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>Lançar despesa no financeiro</FormLabel>
                <p className="text-sm text-muted-foreground">
                  Cria uma transação de despesa (Compra de Material) no valor
                  total real. Não marque se a despesa já foi lançada
                  manualmente.
                </p>
              </div>
            </FormItem>
          )}
        />

        <div className="flex gap-2">
          <LoadingButton type="submit" loading={createMutation.isPending}>
            Registrar Entrada
          </LoadingButton>
          <Button
            type="button"
            variant="outline"
            onClick={() => void navigate({ to: "/estoque/entradas" })}
          >
            Cancelar
          </Button>
        </div>
      </form>
    </Form>
  )
}
