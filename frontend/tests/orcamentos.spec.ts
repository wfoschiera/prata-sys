/**
 * E2E tests for Orçamentos (Quotes) — /orcamentos
 *
 * O1 Superuser creates an orçamento via the UI (client seeded via API) —
 *    success toast, navigates to detail, and it shows up in the list
 * O2 Orçamento detail page renders key document fields
 */
import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

const API_BASE = process.env.VITE_API_URL ?? "http://localhost:8000"

function uniqueName(prefix: string): string {
  return `${prefix} ${Date.now()}-${Math.floor(Math.random() * 9999)}`
}

function randomCpf(): string {
  return Math.random().toString().replace(".", "").slice(0, 11).padEnd(11, "0")
}

async function getToken(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/login/access-token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  })
  const data = (await res.json()) as { access_token: string }
  return data.access_token
}

async function createClientViaApi(
  token: string,
): Promise<{ id: string; name: string }> {
  const name = uniqueName("Orc Cliente")
  const res = await fetch(`${API_BASE}/api/v1/clients/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name,
      document_type: "cpf",
      document_number: randomCpf(),
    }),
  })
  expect(res.status).toBe(201)
  const data = (await res.json()) as { id: string }
  return { id: data.id, name }
}

async function createOrcamentoViaApi(
  token: string,
  clientId: string,
  executionAddress: string,
): Promise<{ id: string }> {
  const res = await fetch(`${API_BASE}/api/v1/orcamentos/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      client_id: clientId,
      service_type: "perfuração",
      execution_address: executionAddress,
    }),
  })
  expect(res.ok).toBeTruthy()
  const data = (await res.json()) as { id: string }
  return { id: data.id }
}

// ---------------------------------------------------------------------------
// O1 create an orçamento through the UI form
// ---------------------------------------------------------------------------

test("O1 superuser creates an orçamento and sees it in the list", async ({
  page,
}) => {
  const token = await getToken(firstSuperuser, firstSuperuserPassword)
  const { name: clientName } = await createClientViaApi(token)
  const address = "Rua dos Orçamentos, 456"

  await page.goto("/orcamentos")
  await expect(page.getByRole("heading", { name: "Orçamentos" })).toBeVisible()

  await page.getByRole("link", { name: "Novo Orçamento" }).click()
  await expect(page).toHaveURL(/\/orcamentos\/new/)

  // Client is a shadcn/Radix Select; open it and pick the seeded client.
  await page.getByLabel("Cliente").click()
  await page.getByRole("option").filter({ hasText: clientName }).first().click()

  await page.getByLabel("Endereço de Execução").fill(address)
  await page.getByRole("button", { name: "Criar Orçamento" }).click()

  await expect(page.getByText("Orçamento criado com sucesso")).toBeVisible()
  // onSuccess navigates to the detail route /orcamentos/<uuid>
  await expect(page).toHaveURL(/\/orcamentos\/[0-9a-f-]{36}/)

  // The list is ordered by created_at desc, so the new orçamento is on page 1.
  await page.goto("/orcamentos")
  await expect(
    page.getByRole("row").filter({ hasText: clientName }),
  ).toBeVisible()
})

// ---------------------------------------------------------------------------
// O2 orçamento detail page renders key fields
// ---------------------------------------------------------------------------

test("O2 orçamento detail page renders key document fields", async ({
  page,
}) => {
  const token = await getToken(firstSuperuser, firstSuperuserPassword)
  const { id: clientId, name: clientName } = await createClientViaApi(token)
  const address = "Av. Detalhe do Orçamento, 789"
  const { id: orcamentoId } = await createOrcamentoViaApi(
    token,
    clientId,
    address,
  )

  await page.goto(`/orcamentos/${orcamentoId}`)

  // Document title heading (exact, to avoid matching "Novo Orçamento")
  await expect(page.getByRole("heading", { name: "Orçamento" })).toBeVisible()
  // Client info block + execution address + totals row
  await expect(page.getByText(clientName)).toBeVisible()
  await expect(page.getByText(address)).toBeVisible()
  await expect(page.getByText("Total geral")).toBeVisible()
})
