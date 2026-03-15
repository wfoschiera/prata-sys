/**
 * OrcamentoListFilters — Filter bar for the orçamento list page.
 *
 * Layout:
 * ┌────────────────┬──────────────┬──────────┬──────────┬─────────┐
 * │ 🔍 Buscar      │ Status ▼     │ De:      │ Até:     │ Limpar  │
 * │ (nome/CPF/CNPJ)│              │ [date]   │ [date]   │         │
 * └────────────────┴──────────────┴──────────┴──────────┴─────────┘
 */

import { Search, X } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type OrcamentoStatus = "rascunho" | "em_analise" | "aprovado" | "cancelado"

interface FilterValues {
  search?: string
  status?: OrcamentoStatus
  dataInicio?: string
  dataFim?: string
}

interface OrcamentoListFiltersProps {
  filters: FilterValues
  onFiltersChange: (filters: FilterValues) => void
}

const STATUS_OPTIONS: { value: OrcamentoStatus; label: string }[] = [
  { value: "rascunho", label: "Rascunho" },
  { value: "em_analise", label: "Em Análise" },
  { value: "aprovado", label: "Aprovado" },
  { value: "cancelado", label: "Cancelado" },
]

export default function OrcamentoListFilters({
  filters,
  onFiltersChange,
}: OrcamentoListFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search ?? "")

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, search: searchInput || undefined })
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput, filters, onFiltersChange]) // eslint-disable-line react-hooks/exhaustive-deps

  const hasFilters =
    filters.search || filters.status || filters.dataInicio || filters.dataFim

  return (
    <div className="flex flex-wrap items-end gap-3">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por nome, CPF ou CNPJ"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pl-8"
        />
      </div>

      {/* Status */}
      <Select
        value={filters.status ?? "all"}
        onValueChange={(val) =>
          onFiltersChange({
            ...filters,
            status: val === "all" ? undefined : (val as OrcamentoStatus),
          })
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos os status</SelectItem>
          {STATUS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Date range */}
      <div className="flex items-center gap-2">
        <Input
          type="date"
          placeholder="De"
          value={filters.dataInicio ?? ""}
          onChange={(e) =>
            onFiltersChange({
              ...filters,
              dataInicio: e.target.value || undefined,
            })
          }
          className="w-[140px]"
        />
        <span className="text-muted-foreground text-sm">até</span>
        <Input
          type="date"
          placeholder="Até"
          value={filters.dataFim ?? ""}
          onChange={(e) =>
            onFiltersChange({
              ...filters,
              dataFim: e.target.value || undefined,
            })
          }
          className="w-[140px]"
        />
      </div>

      {/* Clear */}
      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setSearchInput("")
            onFiltersChange({})
          }}
        >
          <X className="mr-1.5 h-3.5 w-3.5" />
          Limpar filtros
        </Button>
      )}
    </div>
  )
}
