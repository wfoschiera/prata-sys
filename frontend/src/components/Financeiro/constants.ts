export const CATEGORIA_LABELS: Record<string, string> = {
  SERVICO: "Serviço",
  VENDA_EQUIPAMENTO: "Venda de Equipamento",
  RENDIMENTO: "Rendimento",
  CAPITAL_FIXO: "Capital Fixo",
  COMBUSTIVEL: "Combustível",
  MANUTENCAO_EQUIPAMENTO: "Manutenção de Equipamento",
  MANUTENCAO_VEICULO: "Manutenção de Veículo",
  MANUTENCAO_ESCRITORIO: "Manutenção de Escritório",
  COMPRA_MATERIAL: "Compra de Material",
  MO_CLT: "Mão de Obra CLT",
  MO_DIARISTA: "Mão de Obra Diarista",
  ADMIN: "Administrativo",
}

export const INCOME_CATEGORIES: string[] = [
  "SERVICO",
  "VENDA_EQUIPAMENTO",
  "RENDIMENTO",
]

export const EXPENSE_CATEGORIES: string[] = [
  "CAPITAL_FIXO",
  "COMBUSTIVEL",
  "MANUTENCAO_EQUIPAMENTO",
  "MANUTENCAO_VEICULO",
  "MANUTENCAO_ESCRITORIO",
  "COMPRA_MATERIAL",
  "MO_CLT",
  "MO_DIARISTA",
  "ADMIN",
]

export function formatBRL(value: number | string): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(num)
}
