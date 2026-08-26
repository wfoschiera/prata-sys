/**
 * NF-e XML import card for the new-entrada page.
 *
 * Uploads the supplier's XML, shows a preview with per-line product
 * resolution (suggestions are equality-based and non-binding), and hands a
 * prefill payload to the entrada form. Persists nothing — submission stays on
 * the regular create flow.
 */
import { useMutation, useQuery } from "@tanstack/react-query"
import { AlertTriangle, CheckCircle2, FileUp, HelpCircle } from "lucide-react"
import { useRef, useState } from "react"

import {
  EntradasEstoqueService,
  type ImportacaoNfePreview,
  ProductsService,
} from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { AJUSTE_LABELS } from "./custoAquisicao"

export type ImportPrefill = {
  data_entrada: string | undefined
  fornecedor_id: string | undefined
  numero_documento: string
  itens: Array<{
    product_id: string
    quantity: number
    custo_unitario_nf: number
  }>
  ajustes: Array<{
    tipo: string
    valor: number
    documento_referencia: string
    observacao: string
  }>
}

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })

const MATCH_BADGE = {
  sugerido: {
    label: "Sugerido",
    icon: <CheckCircle2 className="h-4 w-4 text-emerald-600" />,
  },
  sem_match: {
    label: "Sem correspondência",
    icon: <HelpCircle className="h-4 w-4 text-amber-600" />,
  },
  ambiguo: {
    label: "Ambíguo",
    icon: <AlertTriangle className="h-4 w-4 text-red-600" />,
  },
} as const

export function ImportarNfeXml({
  onApply,
}: {
  onApply: (prefill: ImportPrefill) => void
}) {
  const { showErrorToast } = useCustomToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<ImportacaoNfePreview | null>(null)
  const [resolutions, setResolutions] = useState<Record<number, string>>({})
  const [includeAjustes, setIncludeAjustes] = useState<Record<number, boolean>>(
    {},
  )

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => ProductsService.listProducts({}),
  })

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const result = await EntradasEstoqueService.importarNfeXml({
        formData: { file },
      })
      return result
    },
    onSuccess: (data) => {
      setPreview(data)
      const initial: Record<number, string> = {}
      data.itens?.forEach((item, idx) => {
        if (item.product_sugerido_id) initial[idx] = item.product_sugerido_id
      })
      setResolutions(initial)
      setIncludeAjustes(
        Object.fromEntries(
          (data.ajustes_sugeridos ?? []).map((_, i) => [i, true]),
        ),
      )
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const itens = preview?.itens ?? []
  const ajustesSugeridos = preview?.ajustes_sugeridos ?? []
  const allResolved =
    itens.length > 0 && itens.every((_, idx) => !!resolutions[idx])

  const handleFileChange = (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    importMutation.mutate(file)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleApply = () => {
    if (!preview) return
    onApply({
      data_entrada: preview.data_entrada || undefined,
      fornecedor_id: preview.fornecedor_sugerido?.id || undefined,
      numero_documento: preview.chave,
      itens: itens.map((item, idx) => ({
        product_id: resolutions[idx],
        quantity: Number(item.quantity),
        custo_unitario_nf: Number(item.custo_unitario_nf),
      })),
      ajustes: ajustesSugeridos
        .map((a, idx) => ({ ...a, included: includeAjustes[idx] !== false }))
        .filter((a) => a.included)
        .map((a) => ({
          tipo: a.tipo,
          valor: Number(a.valor),
          documento_referencia: a.documento_referencia || "",
          observacao: "",
        })),
    })
    setPreview(null)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Importar XML da NF-e</CardTitle>
        <CardDescription>
          Envie o arquivo XML da nota do fornecedor para preencher a entrada
          automaticamente. Confira as correspondências de produto antes de usar
          os dados.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <input
          ref={fileInputRef}
          type="file"
          accept=".xml,text/xml"
          className="hidden"
          onChange={(e) => handleFileChange(e.target.files)}
        />
        <Button
          type="button"
          variant="outline"
          disabled={importMutation.isPending}
          onClick={() => fileInputRef.current?.click()}
        >
          <FileUp className="mr-1.5 h-4 w-4" />
          {importMutation.isPending
            ? "Processando..."
            : "Selecionar arquivo XML"}
        </Button>

        {preview && (
          <div className="space-y-4 rounded-md border p-4">
            {/* Document header */}
            <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
              <div>
                <span className="block text-muted-foreground">Chave</span>
                <span className="break-all font-mono text-xs">
                  {preview.chave}
                </span>
              </div>
              <div>
                <span className="block text-muted-foreground">Nº da nota</span>
                <span>{preview.numero_nota ?? "—"}</span>
              </div>
              <div>
                <span className="block text-muted-foreground">Emissão</span>
                <span>{preview.data_entrada ?? "—"}</span>
              </div>
              <div>
                <span className="block text-muted-foreground">
                  Total da nota
                </span>
                <span>
                  {preview.totals_nota != null
                    ? brl(Number(preview.totals_nota))
                    : "—"}
                </span>
              </div>
            </div>
            {!preview.fornecedor_sugerido && (
              <p className="text-sm text-amber-700">
                CNPJ {preview.emitter_cnpj_digits ?? "—"} não corresponde a
                nenhum fornecedor cadastrado. Selecione o fornecedor no
                formulário abaixo após aplicar.
              </p>
            )}
            {preview.fornecedor_sugerido && (
              <p className="text-sm">
                <span className="text-muted-foreground">Fornecedor: </span>
                {preview.fornecedor_sugerido.company_name}
              </p>
            )}

            {/* Lines with match resolution */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold">Itens da nota</h3>
              {itens.map((item, idx) => {
                const badge = MATCH_BADGE[item.match_status]
                return (
                  <div
                    key={idx}
                    className="grid grid-cols-12 items-center gap-2 rounded-md border p-2 text-sm"
                  >
                    <div className="col-span-5">
                      <span className="font-medium">{item.description}</span>
                      {item.unit && (
                        <span className="ml-1 text-muted-foreground">
                          ({Number(item.quantity)} {item.unit})
                        </span>
                      )}
                    </div>
                    <div className="col-span-2">
                      {brl(Number(item.custo_unitario_nf))}
                    </div>
                    <div className="col-span-2 flex items-center gap-1.5">
                      {badge.icon}
                      <span className="text-xs">{badge.label}</span>
                    </div>
                    <div className="col-span-3">
                      <Select
                        value={resolutions[idx] ?? ""}
                        onValueChange={(v) =>
                          setResolutions((prev) => ({ ...prev, [idx]: v }))
                        }
                      >
                        <SelectTrigger size="sm">
                          <SelectValue placeholder="Produto do estoque" />
                        </SelectTrigger>
                        <SelectContent>
                          {(products ?? []).map((p) => (
                            <SelectItem key={p.id} value={p.id}>
                              {p.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Suggested adjustments */}
            {ajustesSugeridos.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold">
                  Ajustes de custo detectados na nota
                </h3>
                {ajustesSugeridos.map((a, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 rounded-md border p-2 text-sm"
                  >
                    <Checkbox
                      id={`ajuste-${idx}`}
                      checked={includeAjustes[idx] !== false}
                      onCheckedChange={(checked) =>
                        setIncludeAjustes((prev) => ({
                          ...prev,
                          [idx]: checked === true,
                        }))
                      }
                    />
                    <label
                      htmlFor={`ajuste-${idx}`}
                      className="flex flex-1 cursor-pointer items-center gap-3"
                    >
                      <span className="w-40">{AJUSTE_LABELS[a.tipo]}</span>
                      <span className="font-medium">
                        {brl(Number(a.valor))}
                      </span>
                    </label>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <Button
                type="button"
                disabled={!allResolved}
                onClick={handleApply}
              >
                Usar dados importados
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setPreview(null)}
              >
                Descartar
              </Button>
            </div>
            {!allResolved && (
              <p className="text-sm text-muted-foreground">
                Resolva todas as correspondências de produto para continuar.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
