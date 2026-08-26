/**
 * Client-side mirror of the backend's cost apportionment, used only to preview
 * the real unit cost while a user fills in the entrada form.
 *
 * The backend in `crud._apportion_ajustes` remains the source of truth — this is
 * a display aid. Keep the two in sync: value share, centavo rounding, residual
 * to the largest lot, quantity-share fallback when the entrada has no value.
 */
import type { TipoCustoAjuste } from "@/client"

export const TIPO_AJUSTE_OPTIONS: TipoCustoAjuste[] = [
  "frete",
  "seguro",
  "icms_st",
  "ipi",
  "despesa_acessoria",
  "desconto_comercial",
  "devolucao",
  "correcao_documento",
  "outros",
]

export const AJUSTE_LABELS: Record<string, string> = {
  frete: "Frete",
  seguro: "Seguro",
  icms_st: "ICMS-ST",
  ipi: "IPI",
  despesa_acessoria: "Despesa Acessória",
  desconto_comercial: "Desconto Comercial",
  devolucao: "Devolução",
  correcao_documento: "Correção de Documento",
  outros: "Outros",
}

/** Types that reduce cost and therefore must carry a negative valor. */
const NEGATIVE_TIPOS = new Set(["desconto_comercial", "devolucao"])

export function isNegativeTipo(tipo: string): boolean {
  return NEGATIVE_TIPOS.has(tipo)
}

export interface ApportionInput {
  key: string
  quantity: number
  custoUnitario: number
}

const round2 = (v: number) => Math.round((v + Number.EPSILON) * 100) / 100

/**
 * Distribute `totalAjustes` across lots by value share. The rounding residual
 * goes to the largest lot so the shares always sum to the total exactly.
 */
export function apportionAjustes(
  itens: ApportionInput[],
  totalAjustes: number,
): Record<string, number> {
  if (itens.length === 0) return {}

  const valores = itens.map((i) => ({
    key: i.key,
    base: (i.quantity || 0) * (i.custoUnitario || 0),
  }))
  let baseTotal = valores.reduce((acc, v) => acc + v.base, 0)
  let ranking = valores

  if (baseTotal <= 0) {
    // All-bonificação delivery: fall back to quantity share.
    ranking = itens.map((i) => ({ key: i.key, base: i.quantity || 0 }))
    baseTotal = ranking.reduce((acc, v) => acc + v.base, 0)
    if (baseTotal <= 0) {
      return Object.fromEntries(itens.map((i) => [i.key, 0]))
    }
  }

  const shares: Record<string, number> = {}
  for (const v of ranking) {
    shares[v.key] = round2(totalAjustes * (v.base / baseTotal))
  }

  const assigned = Object.values(shares).reduce((acc, v) => acc + v, 0)
  const residual = round2(round2(totalAjustes) - assigned)
  if (residual !== 0) {
    const largest = ranking.reduce((a, b) => (b.base > a.base ? b : a))
    shares[largest.key] = round2(shares[largest.key] + residual)
  }
  return shares
}

/** Invoice unit cost plus this lot's apportioned share of the adjustments. */
export function custoUnitarioReal(
  quantity: number,
  custoUnitarioNf: number,
  share: number,
): number {
  if (!quantity || quantity <= 0) return 0
  return (custoUnitarioNf * quantity + share) / quantity
}
