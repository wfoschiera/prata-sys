/**
 * E2E tests for Phase 4 Finance Flows (tasks 14.3–14.10)
 *
 * 14.3 Finance user creates a receita — appears in transactions list
 * 14.4 Finance user creates a despesa with categoria=COMBUSTIVEL — appears under Despesas
 * 14.5 Attempt to create a despesa with categoria=SERVICO returns 422
 * 14.6 Finance Dashboard KPI cards show correct totals for current month
 * 14.7 6-month bar chart renders with monthly labels and grouped bars
 * 14.8 Admin user (view_financeiro, no manage_financeiro) cannot create transactions
 * 14.9 Client user sees no finance sidebar links
 * 14.10 Deleting a service leaves linked transactions with service_id=null
 */
import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.VITE_API_URL ?? "http://localhost:8000"

async function getToken(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/login/access-token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  })
  const data = (await res.json()) as { access_token: string }
  return data.access_token
}

async function createUserWithRole(
  superToken: string,
  role: "finance" | "admin" | "client",
): Promise<{ email: string; password: string }> {
  const email = randomEmail()
  const password = randomPassword() + "A1!" // ensure enough entropy
  await fetch(`${API_BASE}/api/v1/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      email,
      password,
      full_name: `Test ${role} user`,
      is_verified: true,
      role,
    }),
  })
  return { email, password }
}

// ---------------------------------------------------------------------------
// 14.3 Finance user creates a receita — appears in transactions list
// ---------------------------------------------------------------------------

test("14.3 finance user creates receita — appears in transactions list", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")
  await logInUser(page, email, password)

  await page.goto("/financeiro/transacoes")
  await expect(page.getByRole("heading", { name: /Transações/i })).toBeVisible()

  await page.getByRole("button", { name: "Nova Transação" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  // Select categoria (tipo defaults to "receita")
  const selects = page.getByRole("combobox")
  await selects.nth(1).click()
  await page.getByRole("option", { name: "Serviço" }).click()

  // Fill valor
  await page.getByLabel(/Valor/i).fill("1500")

  // Submit
  await page.getByRole("button", { name: "Salvar" }).click()

  await expect(page.getByText("Transação criada com sucesso")).toBeVisible()
  await expect(page.getByRole("dialog")).not.toBeVisible()

  // Row with Serviço category appears in the table
  await expect(
    page.getByRole("cell", { name: /Serviço/i }).first(),
  ).toBeVisible()
})

// ---------------------------------------------------------------------------
// 14.4 Finance user creates despesa COMBUSTIVEL — appears under Despesas
// ---------------------------------------------------------------------------

test("14.4 finance user creates despesa COMBUSTIVEL — appears under Despesas", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")
  await logInUser(page, email, password)

  await page.goto("/financeiro/contas-a-pagar")
  await expect(page.getByRole("heading", { name: /Despesas/i })).toBeVisible()

  await page.getByRole("button", { name: "Nova Despesa" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  // Categoria — tipo is locked to "despesa"; select Combustível
  const selects = page.getByRole("combobox")
  await selects.nth(1).click()
  await page.getByRole("option", { name: "Combustível" }).click()

  await page.getByLabel(/Valor/i).fill("300")

  await page.getByRole("button", { name: "Salvar" }).click()

  await expect(page.getByText("Transação criada com sucesso")).toBeVisible()
  await expect(page.getByRole("dialog")).not.toBeVisible()

  await expect(
    page.getByRole("cell", { name: /Combustível/i }).first(),
  ).toBeVisible()
})

// ---------------------------------------------------------------------------
// 14.5 Despesa with categoria=SERVICO (income-only) rejected with 422
// ---------------------------------------------------------------------------

test("14.5 despesa with categoria SERVICO is rejected by API with 422", async () => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")
  const token = await getToken(email, password)
  const today = new Date().toISOString().split("T")[0]

  const res = await fetch(`${API_BASE}/api/v1/transacoes/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      tipo: "despesa",
      categoria: "SERVICO",
      valor: 100,
      data_competencia: today,
    }),
  })

  expect(res.status).toBe(422)
})

// ---------------------------------------------------------------------------
// 14.6 Finance Dashboard KPI cards display for current month
// ---------------------------------------------------------------------------

test("14.6 dashboard KPI cards show Receitas, Despesas, Resultado Líquido", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")
  await logInUser(page, email, password)

  await page.goto("/financeiro")

  await expect(page.getByText(/Receitas/i).first()).toBeVisible({
    timeout: 10000,
  })
  await expect(page.getByText(/Despesas/i).first()).toBeVisible()
  await expect(page.getByText(/Resultado Líquido/i)).toBeVisible()
})

// ---------------------------------------------------------------------------
// 14.7 Finance Dashboard 6-month bar chart renders
// ---------------------------------------------------------------------------

test("14.7 dashboard renders a bar chart with 6 month labels", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")
  await logInUser(page, email, password)

  await page.goto("/financeiro")

  // Recharts renders an SVG
  await expect(page.locator("svg").first()).toBeVisible({ timeout: 10000 })

  // At least 6 month abbreviations should appear on the chart
  const monthLabels = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
  ]
  let foundCount = 0
  for (const label of monthLabels) {
    foundCount += await page.getByText(label, { exact: true }).count()
  }
  expect(foundCount).toBeGreaterThanOrEqual(6)
})

// ---------------------------------------------------------------------------
// 14.8 Admin user can view but NOT create transactions
// ---------------------------------------------------------------------------

test("14.8 admin-role user sees finance pages but has no Nova Transação button", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "admin")
  await logInUser(page, email, password)

  await page.goto("/financeiro/transacoes")
  await expect(page.getByRole("heading", { name: /Transações/i })).toBeVisible()

  // Admin has view_financeiro but NOT manage_financeiro
  await expect(
    page.getByRole("button", { name: "Nova Transação" }),
  ).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// 14.9 Client user sees no finance sidebar links
// ---------------------------------------------------------------------------

test.describe("14.9 client user has no finance sidebar links", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("client role sees no Financeiro section in sidebar", async ({
    page,
  }) => {
    const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
    const { email, password } = await createUserWithRole(superToken, "client")
    await logInUser(page, email, password)

    await expect(
      page.getByRole("link", { name: /Dashboard Financeiro/i }),
    ).not.toBeVisible()
    await expect(
      page.getByRole("link", { name: "Transações" }),
    ).not.toBeVisible()
    await expect(page.getByRole("link", { name: "Despesas" })).not.toBeVisible()
    await expect(page.getByRole("link", { name: "Receitas" })).not.toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// 14.10 Deleting a service nullifies service_id on linked transactions
// ---------------------------------------------------------------------------

test("14.10 deleting a service sets service_id to null on linked transactions", async () => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const today = new Date().toISOString().split("T")[0]

  // Create client
  const clientRes = await fetch(`${API_BASE}/api/v1/clients/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      name: "Test Client 14.10",
      document_type: "cpf",
      document_number: "11122233344",
    }),
  })
  const client = (await clientRes.json()) as { id: string }

  // Create service
  const serviceRes = await fetch(`${API_BASE}/api/v1/services/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      type: "perfuração",
      client_id: client.id,
      execution_address: "Rua Teste, 1, Cidade SP",
    }),
  })
  const service = (await serviceRes.json()) as { id: string }

  // Create transaction linked to service
  const txRes = await fetch(`${API_BASE}/api/v1/transacoes/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      tipo: "receita",
      categoria: "SERVICO",
      valor: 500,
      data_competencia: today,
      service_id: service.id,
    }),
  })
  const tx = (await txRes.json()) as { id: string; service_id: string | null }
  expect(tx.service_id).toBe(service.id)

  // Delete the service
  const delRes = await fetch(`${API_BASE}/api/v1/services/${service.id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${superToken}` },
  })
  expect(delRes.status).toBe(200)

  // Fetch transaction again — service_id must be null
  const txAfterRes = await fetch(`${API_BASE}/api/v1/transacoes/${tx.id}`, {
    headers: { Authorization: `Bearer ${superToken}` },
  })
  const txAfter = (await txAfterRes.json()) as { service_id: string | null }
  expect(txAfter.service_id).toBeNull()
})
