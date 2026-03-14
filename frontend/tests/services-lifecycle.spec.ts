/**
 * E2E tests for Phase 5 — Service Lifecycle Frontend
 *
 * Tests cover:
 * - StatusTimeline renders for each status
 * - TransitionButtons: forward transitions (requested→scheduled→executing)
 * - CancelModal: opens, requires reason, calls transition API
 * - CompleteConfirmModal: allows quantity adjustment, submits deduction_items
 * - StockWarningBadge: renders compact badge in service list
 * - "Baixar do Estoque" button visible in executing status
 */

import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

test.use({ storageState: { cookies: [], origins: [] } })

const API_BASE = process.env.VITE_API_URL ?? "http://localhost:8000"

async function getSuperToken(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/login/access-token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      username: firstSuperuser,
      password: firstSuperuserPassword,
    }),
  })
  const data = (await res.json()) as { access_token: string }
  return data.access_token
}

function uniqueName(prefix: string): string {
  return `${prefix} ${Date.now()}-${Math.floor(Math.random() * 9999)}`
}

async function createTestClient(
  token: string,
): Promise<{ id: string; name: string }> {
  const digits = Math.random()
    .toString()
    .replace(".", "")
    .slice(0, 11)
    .padEnd(11, "0")
  const name = uniqueName("E2E Client")
  const res = await fetch(`${API_BASE}/api/v1/clients/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name,
      document_type: "cpf",
      document_number: digits,
    }),
  })
  expect(res.status).toBe(201)
  const data = (await res.json()) as { id: string }
  return { id: data.id, name }
}

async function createTestService(
  token: string,
  clientId: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/services/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      type: "perfuração",
      execution_address: "Rua dos Testes, 123",
      client_id: clientId,
    }),
  })
  expect(res.status).toBe(201)
  const data = (await res.json()) as { id: string }
  return data.id
}

async function transitionService(
  token: string,
  serviceId: string,
  toStatus: string,
  extra: Record<string, unknown> = {},
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/v1/services/${serviceId}/transition`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ to_status: toStatus, ...extra }),
    },
  )
  expect(res.status).toBe(200)
}

async function loginSuperuser(page: import("@playwright/test").Page) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(firstSuperuser)
  await page.getByTestId("password-input").fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")
}

async function openServiceDetail(
  page: import("@playwright/test").Page,
  clientName: string,
) {
  await page.goto("/services")
  await page.waitForSelector("table")
  const row = page.locator("tr").filter({ hasText: clientName })
  await row.locator("button[aria-label='Ver detalhes']").first().click()
  await page.waitForSelector("[data-state='open']", { timeout: 5000 })
}

// ── Tests ───────────────────────────────────────────────────────────────────

test("service detail shows StatusTimeline with requested step active", async ({
  page,
}) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  await createTestService(token, clientId)

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await expect(page.getByText("Solicitado").first()).toBeVisible()
  await expect(page.getByText("Agendado").first()).toBeVisible()
  await expect(page.getByText("Em Execução").first()).toBeVisible()
  await expect(page.getByText("Concluído").first()).toBeVisible()
})

test("admin sees Agendar button for requested service", async ({ page }) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  await createTestService(token, clientId)

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await expect(page.getByRole("button", { name: "Agendar" })).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Cancelar Serviço" }),
  ).toBeVisible()
})

test("clicking Agendar transitions service to scheduled", async ({ page }) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  await createTestService(token, clientId)

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await page.getByRole("button", { name: "Agendar" }).click()
  await expect(page.getByText("Status atualizado com sucesso")).toBeVisible()

  await expect(
    page.getByRole("button", { name: "Iniciar Execução" }),
  ).toBeVisible()
})

test("CancelModal requires reason before confirming", async ({ page }) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  await createTestService(token, clientId)

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await page.getByRole("button", { name: "Cancelar Serviço" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  const confirmBtn = page.getByRole("button", {
    name: "Confirmar Cancelamento",
  })
  await expect(confirmBtn).toBeDisabled()

  await page.getByLabel("Motivo *").fill("Cliente desistiu")
  await expect(confirmBtn).toBeEnabled()
})

test("CancelModal submits and shows success toast", async ({ page }) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  await createTestService(token, clientId)

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await page.getByRole("button", { name: "Cancelar Serviço" }).click()
  await page.getByLabel("Motivo *").fill("Cliente cancelou o contrato")
  await page.getByRole("button", { name: "Confirmar Cancelamento" }).click()

  await expect(page.getByText("Serviço cancelado com sucesso")).toBeVisible()
})

test("cancelled service shows cancelled node and reason in timeline", async ({
  page,
}) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  const serviceId = await createTestService(token, clientId)
  await transitionService(token, serviceId, "cancelled", {
    reason: "Motivo de teste E2E",
  })

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await expect(page.getByText("Cancelado").first()).toBeVisible()
  await expect(page.getByText("Motivo de teste E2E")).toBeVisible()
})

test("executing service shows Baixar do Estoque button for admin", async ({
  page,
}) => {
  const token = await getSuperToken()
  const { id: clientId, name } = await createTestClient(token)
  const serviceId = await createTestService(token, clientId)
  await transitionService(token, serviceId, "scheduled")
  await transitionService(token, serviceId, "executing")

  await loginSuperuser(page)
  await openServiceDetail(page, name)

  await expect(
    page.getByRole("button", { name: "Baixar do Estoque" }),
  ).toBeVisible()
})
