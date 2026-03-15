/**
 * OrcamentoDetail — Full document view for a single orçamento.
 *
 * Design direction: "Professional Document with Digital Soul"
 * The document area uses a clean, paper-like aesthetic with subtle borders
 * and structured sections. The action bar floats above as a utility strip.
 * Print view (@media print) strips all chrome, leaving only the document.
 *
 * Layout:
 * ┌─────────────────────────────────────────────────┐
 * │ ← Voltar    [Status Badge]    [Action Buttons]  │  ← sticky bar (no-print)
 * ├─────────────────────────────────────────────────┤
 * │  ┌─────────────────────────────────────────┐    │
 * │  │ COMPANY HEADER (logo + details)         │    │
 * │  ├─────────────────────────────────────────┤    │
 * │  │ CLIENT INFO BLOCK                       │    │
 * │  ├─────────────────────────────────────────┤    │
 * │  │ ORÇAMENTO #A3F2C1        Data: 14/03/26│    │
 * │  ├──────┬─────────────┬─────────┬──────────┤    │
 * │  │ Qtde │ Descrição   │ R$ Unit │ R$ Total │    │
 * │  ├──────┼─────────────┼─────────┼──────────┤    │
 * │  │ ...  │ ...         │ ...     │ ...      │    │
 * │  ├──────┴─────────────┴─────────┼──────────┤    │
 * │  │                    Total geral│ R$ XXXXX │    │
 * │  ├─────────────────────────────────────────┤    │
 * │  │ Forma de pagamento: ...                 │    │
 * │  │ Validade: ...   │   Vendedor: ...       │    │
 * │  └─────────────────────────────────────────┘    │
 * ├─────────────────────────────────────────────────┤
 * │ STATUS LOG TIMELINE (no-print)                  │
 * └─────────────────────────────────────────────────┘
 */

import { Link } from "@tanstack/react-router"
import {
  ArrowLeft,
  CheckCircle2,
  ClipboardCopy,
  FileText,
  Printer,
  Send,
  Wrench,
  XCircle,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

// ── Types ─────────────────────────────────────────────────────────────────────

type OrcamentoStatus = "rascunho" | "em_analise" | "aprovado" | "cancelado"

interface OrcamentoItem {
  id: string
  product_id: string
  description: string
  quantity: number
  unit_price: number
  show_unit_price: boolean
}

interface StatusLogEntry {
  id: string
  from_status: OrcamentoStatus
  to_status: OrcamentoStatus
  changed_by_user?: { email: string }
  changed_at: string
  notes?: string | null
}

interface CompanySettings {
  company_name: string
  cnpj?: string | null
  inscricao_municipal?: string | null
  address?: string | null
  phone?: string | null
  email?: string | null
  logo_url?: string | null
}

interface OrcamentoData {
  id: string
  ref_code: string
  status: OrcamentoStatus
  service_type: "perfuração" | "reparo"
  description?: string | null
  notes?: string | null
  execution_address: string
  city?: string | null
  cep?: string | null
  forma_pagamento?: string | null
  validade_proposta?: string | null
  vendedor?: string | null
  service_id?: string | null
  created_at: string
  client: {
    id: string
    name: string
    document_type: "cpf" | "cnpj"
    document_number: string
    email?: string | null
    phone?: string | null
    address?: string | null
    bairro?: string | null
    city?: string | null
    state?: string | null
    cep?: string | null
  }
  items: OrcamentoItem[]
  status_logs: StatusLogEntry[]
}

// ── Constants ─────────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<OrcamentoStatus, string> = {
  rascunho: "Rascunho",
  em_analise: "Em Análise",
  aprovado: "Aprovado",
  cancelado: "Cancelado",
}

const STATUS_COLORS: Record<
  OrcamentoStatus,
  { bg: string; text: string; border: string }
> = {
  rascunho: {
    bg: "bg-zinc-100",
    text: "text-zinc-700",
    border: "border-zinc-300",
  },
  em_analise: {
    bg: "bg-amber-50",
    text: "text-amber-800",
    border: "border-amber-300",
  },
  aprovado: {
    bg: "bg-emerald-50",
    text: "text-emerald-800",
    border: "border-emerald-300",
  },
  cancelado: {
    bg: "bg-red-50",
    text: "text-red-800",
    border: "border-red-300",
  },
}

const VALID_TRANSITIONS: Record<OrcamentoStatus, OrcamentoStatus[]> = {
  rascunho: ["em_analise", "cancelado"],
  em_analise: ["rascunho", "aprovado", "cancelado"],
  aprovado: ["em_analise", "cancelado"],
  cancelado: [],
}

const TRANSITION_CONFIG: Record<
  OrcamentoStatus,
  {
    label: string
    icon: React.ReactNode
    variant: "default" | "outline" | "destructive"
  }
> = {
  rascunho: {
    label: "Voltar p/ Rascunho",
    icon: <FileText className="mr-1.5 h-3.5 w-3.5" />,
    variant: "outline",
  },
  em_analise: {
    label: "Enviar p/ Análise",
    icon: <Send className="mr-1.5 h-3.5 w-3.5" />,
    variant: "outline",
  },
  aprovado: {
    label: "Aprovar",
    icon: <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" />,
    variant: "default",
  },
  cancelado: {
    label: "Cancelar",
    icon: <XCircle className="mr-1.5 h-3.5 w-3.5" />,
    variant: "destructive",
  },
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR")
}

function formatQuantity(qty: number): string {
  return Number.isInteger(qty) ? String(qty) : qty.toLocaleString("pt-BR")
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function CompanyHeader({ company }: { company: CompanySettings }) {
  return (
    <div className="flex items-start gap-4 border-b border-zinc-300 pb-4">
      {company.logo_url && (
        <img
          src={company.logo_url}
          alt={company.company_name}
          className="h-16 w-auto object-contain"
        />
      )}
      <div className="flex-1 text-center">
        <h2 className="text-sm font-bold uppercase tracking-wide text-zinc-900">
          {company.company_name}
        </h2>
        {company.cnpj && (
          <p className="text-xs text-zinc-600">
            CNPJ: {company.cnpj}
            {company.inscricao_municipal &&
              ` | Inscrição municipal: ${company.inscricao_municipal}`}
          </p>
        )}
        {company.address && (
          <p className="text-xs text-zinc-600">{company.address}</p>
        )}
        <p className="text-xs text-zinc-600">
          {[
            company.phone && `FONE: ${company.phone}`,
            company.email && `E-mail: ${company.email}`,
          ]
            .filter(Boolean)
            .join(" | ")}
        </p>
      </div>
    </div>
  )
}

function ClientInfoBlock({
  client,
  executionAddress,
  city,
  cep,
}: {
  client: OrcamentoData["client"]
  executionAddress: string
  city?: string | null
  cep?: string | null
}) {
  const docLabel = client.document_type === "cpf" ? "CPF" : "CNPJ"

  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-1 border-b border-zinc-300 py-3 text-sm">
      <div>
        <span className="text-zinc-500 text-xs">Nome:</span>{" "}
        <span className="font-medium text-zinc-900">{client.name}</span>
      </div>
      <div>
        <span className="text-zinc-500 text-xs">{docLabel}:</span>{" "}
        <span className="font-mono text-zinc-900">
          {client.document_number}
        </span>
      </div>

      <div>
        <span className="text-zinc-500 text-xs">Endereço:</span>{" "}
        <span className="text-zinc-800">{executionAddress}</span>
      </div>
      <div>
        <span className="text-zinc-500 text-xs">Bairro:</span>{" "}
        <span className="text-zinc-800">{client.bairro ?? "—"}</span>
      </div>

      <div>
        <span className="text-zinc-500 text-xs">Cidade:</span>{" "}
        <span className="text-zinc-800">{city ?? client.city ?? "—"}</span>
      </div>
      <div>
        <span className="text-zinc-500 text-xs">CEP:</span>{" "}
        <span className="font-mono text-zinc-800">
          {cep ?? client.cep ?? "—"}
        </span>
      </div>

      <div>
        <span className="text-zinc-500 text-xs">Telefone:</span>{" "}
        <span className="text-zinc-800">{client.phone ?? "—"}</span>
      </div>
      <div>
        <span className="text-zinc-500 text-xs">E-mail:</span>{" "}
        <span className="text-zinc-800">{client.email ?? "—"}</span>
      </div>
    </div>
  )
}

function ItemsTable({ items }: { items: OrcamentoItem[] }) {
  const grandTotal = items.reduce(
    (sum, item) => sum + item.quantity * item.unit_price,
    0,
  )

  return (
    <Table>
      <TableHeader>
        <TableRow className="bg-zinc-50 hover:bg-zinc-50">
          <TableHead className="w-[80px] text-right font-semibold text-zinc-700">
            Qtde
          </TableHead>
          <TableHead className="font-semibold text-zinc-700">
            Descrição
          </TableHead>
          <TableHead className="w-[130px] text-right font-semibold text-zinc-700">
            R$ Unit.
          </TableHead>
          <TableHead className="w-[140px] text-right font-semibold text-zinc-700">
            R$ Total
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id} className="hover:bg-zinc-50/50">
            <TableCell className="text-right font-mono text-sm">
              {formatQuantity(item.quantity)}
            </TableCell>
            <TableCell className="text-sm text-zinc-800">
              {item.description}
            </TableCell>
            <TableCell className="text-right font-mono text-sm">
              {item.show_unit_price ? formatCurrency(item.unit_price) : "—"}
            </TableCell>
            <TableCell className="text-right font-mono text-sm font-medium">
              {formatCurrency(item.quantity * item.unit_price)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
      <TableFooter>
        <TableRow className="bg-zinc-50 font-bold">
          <TableCell colSpan={3} className="text-right text-zinc-600">
            Total geral
          </TableCell>
          <TableCell className="text-right font-mono text-base text-zinc-900">
            {formatCurrency(grandTotal)}
          </TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  )
}

function DocumentFooter({
  formaPagamento,
  validadeProposta,
  vendedor,
}: {
  formaPagamento?: string | null
  validadeProposta?: string | null
  vendedor?: string | null
}) {
  return (
    <div className="border-t border-zinc-300 pt-3 text-sm space-y-1.5">
      {formaPagamento && (
        <div>
          <span className="text-zinc-500 text-xs">Forma de pagamento:</span>{" "}
          <span className="text-zinc-800">{formaPagamento}</span>
        </div>
      )}
      <div className="flex justify-between">
        {validadeProposta && (
          <div>
            <span className="text-zinc-500 text-xs">Validade da proposta:</span>{" "}
            <span className="text-zinc-800">
              {formatDate(validadeProposta)}
            </span>
          </div>
        )}
        {vendedor && (
          <div>
            <span className="text-zinc-500 text-xs">Vendedor:</span>{" "}
            <span className="text-zinc-800">{vendedor}</span>
          </div>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: OrcamentoStatus }) {
  const colors = STATUS_COLORS[status]
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold ${colors.bg} ${colors.text} ${colors.border}`}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}

function StatusLogTimeline({ logs }: { logs: StatusLogEntry[] }) {
  if (logs.length === 0) return null

  return (
    <div className="no-print space-y-3">
      <h3 className="text-sm font-semibold text-zinc-700">
        Histórico de alterações
      </h3>
      <div className="relative border-l-2 border-zinc-200 pl-4 space-y-3">
        {logs.map((log) => (
          <div key={log.id} className="relative">
            <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-zinc-400 border-2 border-white" />
            <div className="text-sm">
              <span className="font-medium text-zinc-700">
                {STATUS_LABELS[log.from_status]}
              </span>
              <span className="text-zinc-400 mx-1">→</span>
              <span className="font-medium text-zinc-700">
                {STATUS_LABELS[log.to_status]}
              </span>
              <span className="text-zinc-400 text-xs ml-2">
                {new Date(log.changed_at).toLocaleString("pt-BR")}
              </span>
              {log.changed_by_user && (
                <span className="text-zinc-400 text-xs ml-1">
                  por {log.changed_by_user.email}
                </span>
              )}
            </div>
            {log.notes && (
              <p className="text-xs text-zinc-500 mt-0.5 italic">{log.notes}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

interface OrcamentoDetailProps {
  orcamento: OrcamentoData
  company: CompanySettings
  onTransition: (toStatus: OrcamentoStatus, reason?: string) => void
  onConvertToService: () => void
  onDuplicate: () => void
  isTransitioning?: boolean
  isConverting?: boolean
  isDuplicating?: boolean
}

export default function OrcamentoDetail({
  orcamento,
  company,
  onTransition,
  onConvertToService,
  onDuplicate,
  isTransitioning = false,
  isConverting = false,
  isDuplicating = false,
}: OrcamentoDetailProps) {
  const validTransitions = VALID_TRANSITIONS[orcamento.status]
  // const canEdit — re-enable with edit page
  const canConvert = orcamento.status === "aprovado" && !orcamento.service_id
  const hasService = !!orcamento.service_id

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      {/* ── Action bar (hidden on print) ─────────────────────────────── */}
      <div className="no-print flex flex-wrap items-center justify-between gap-3 sticky top-0 z-10 bg-background/95 backdrop-blur-sm py-3 -mx-1 px-1 border-b border-zinc-100">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/orcamentos">
              <ArrowLeft className="mr-1.5 h-4 w-4" />
              Voltar
            </Link>
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <StatusBadge status={orcamento.status} />
          <span className="text-xs text-muted-foreground font-mono">
            #{orcamento.ref_code}
          </span>
        </div>

        <TooltipProvider>
          <div className="flex items-center gap-1.5">
            {/* Status transitions */}
            {validTransitions.map((target) => {
              const config = TRANSITION_CONFIG[target]
              return (
                <Tooltip key={target}>
                  <TooltipTrigger asChild>
                    <Button
                      variant={config.variant}
                      size="sm"
                      onClick={() => onTransition(target)}
                      disabled={isTransitioning}
                    >
                      {config.icon}
                      {config.label}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Alterar status para "{STATUS_LABELS[target]}"
                  </TooltipContent>
                </Tooltip>
              )
            })}

            {validTransitions.length > 0 && (
              <Separator orientation="vertical" className="h-5 mx-1" />
            )}

            {/* Convert to Service */}
            {canConvert && (
              <Button
                variant="default"
                size="sm"
                onClick={onConvertToService}
                disabled={isConverting}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                <Wrench className="mr-1.5 h-3.5 w-3.5" />
                Criar Serviço
              </Button>
            )}

            {/* Service already created */}
            {hasService && (
              <Badge
                variant="outline"
                className="text-emerald-700 border-emerald-300 bg-emerald-50"
              >
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Serviço criado
              </Badge>
            )}

            {/* TODO: Edit page (Wave D) */}

            {/* Duplicate */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDuplicate}
                  disabled={isDuplicating}
                >
                  <ClipboardCopy className="mr-1.5 h-3.5 w-3.5" />
                  Duplicar
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Criar uma cópia deste orçamento como rascunho
              </TooltipContent>
            </Tooltip>

            {/* Print */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => window.print()}
                >
                  <Printer className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Imprimir orçamento</TooltipContent>
            </Tooltip>
          </div>
        </TooltipProvider>
      </div>

      {/* ── Document body (printed) ──────────────────────────────────── */}
      <div className="orcamento-doc bg-white border border-zinc-200 rounded-lg shadow-sm p-8 space-y-4">
        {/* Company header */}
        <CompanyHeader company={company} />

        {/* Client info */}
        <ClientInfoBlock
          client={orcamento.client}
          executionAddress={orcamento.execution_address}
          city={orcamento.city}
          cep={orcamento.cep}
        />

        {/* Document title + date */}
        <div className="flex items-baseline justify-between border-b border-zinc-300 pb-2">
          <h1 className="text-lg font-bold uppercase tracking-wider text-zinc-900">
            Orçamento
          </h1>
          <div className="text-sm text-zinc-600">
            <span className="text-zinc-500">Data:</span>{" "}
            <span className="font-medium">
              {formatDate(orcamento.created_at)}
            </span>
          </div>
        </div>

        {/* Description */}
        {orcamento.description && (
          <p className="text-sm text-zinc-600 italic">
            {orcamento.description}
          </p>
        )}

        {/* Items table */}
        <ItemsTable items={orcamento.items} />

        {/* Footer */}
        <DocumentFooter
          formaPagamento={orcamento.forma_pagamento}
          validadeProposta={orcamento.validade_proposta}
          vendedor={orcamento.vendedor}
        />
      </div>

      {/* ── Status log (hidden on print) ─────────────────────────────── */}
      <StatusLogTimeline logs={orcamento.status_logs} />
    </div>
  )
}
