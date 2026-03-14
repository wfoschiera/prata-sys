/**
 * E2E tests for Phase 6 Fornecedores (Suppliers)
 *
 * F1 Superuser creates a fornecedor — appears in list
 * F2 Superuser adds a contact to a fornecedor
 * F3 Superuser edits a fornecedor's categories via checkbox toggle
 * F4 Finance user can view fornecedores list but cannot create
 * F5 Client user does not see Fornecedores in sidebar
 * F6 Invalid CNPJ shows validation error
 * F7 Delete fornecedor removes it from list
 */
import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

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
  const password = `${randomPassword()}A1!`
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

async function switchUser(
  page: import("@playwright/test").Page,
  email: string,
  password: string,
) {
  await logInUser(page, email, password)
}

// ---------------------------------------------------------------------------
// F1 Superuser creates a fornecedor — appears in list
// ---------------------------------------------------------------------------

test("F1 superuser creates fornecedor — appears in list", async ({ page }) => {
  await switchUser(page, firstSuperuser, firstSuperuserPassword)

  await page.goto("/fornecedores")
  await expect(
    page.getByRole("heading", { name: /Fornecedores/i }),
  ).toBeVisible()

  await page.getByRole("button", { name: "Novo Fornecedor" }).click()
  await expect(page).toHaveURL(/\/fornecedores\/new/)

  await page.getByLabel(/Nome da Empresa/i).fill("Empresa Teste Ltda")
  await page.getByRole("button", { name: "Criar Fornecedor" }).click()

  await expect(page.getByText("Fornecedor criado")).toBeVisible()
  await page.goto("/fornecedores")
  await expect(page.getByText("Empresa Teste Ltda")).toBeVisible()
})

// ---------------------------------------------------------------------------
// F2 Superuser adds a contact to a fornecedor
// ---------------------------------------------------------------------------

test("F2 superuser adds contact to fornecedor", async ({ page }) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  // Create fornecedor via API
  const res = await fetch(`${API_BASE}/api/v1/fornecedores`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      company_name: "Contato Test Supplier",
      categories: [],
      contatos: [],
    }),
  })
  const fornecedor = (await res.json()) as { id: string }

  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto(`/fornecedores/${fornecedor.id}`)
  await expect(page.getByText("Contato Test Supplier")).toBeVisible()

  await page.getByRole("button", { name: "Adicionar" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  await page.getByLabel(/^Nome$/i).fill("João Silva")
  await page.getByLabel(/Cargo \/ Função/i).fill("Gerente")
  await page.getByLabel(/^Telefone$/i).fill("11999999999")
  // Submit button says "Adicionar" when creating a new contact
  await page.getByRole("button", { name: "Adicionar" }).last().click()

  await expect(page.getByRole("dialog")).not.toBeVisible()
  await expect(page.getByText("João Silva")).toBeVisible()
})

// ---------------------------------------------------------------------------
// F3 Superuser toggles categories on fornecedor
// ---------------------------------------------------------------------------

test("F3 superuser toggles category on fornecedor", async ({ page }) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  const res = await fetch(`${API_BASE}/api/v1/fornecedores`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      company_name: "Category Test Supplier",
      categories: [],
      contatos: [],
    }),
  })
  const fornecedor = (await res.json()) as { id: string }

  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto(`/fornecedores/${fornecedor.id}`)
  await expect(page.getByText("Category Test Supplier")).toBeVisible()

  // Wait for the Categorias section to render (it only shows for existing records)
  await expect(page.getByRole("heading", { name: "Categorias" })).toBeVisible()

  // Wait for the PATCH request triggered by toggling the Tubos label
  // (Radix UI Checkbox responds to label click; wait for API response before reloading)
  const [response] = await Promise.all([
    page.waitForResponse(
      (res) =>
        res.url().includes("/fornecedores/") &&
        res.request().method() === "PATCH",
    ),
    page.getByText("Tubos").click(),
  ])
  await expect(response.status()).toBe(200)

  // Reload and verify it persisted
  await page.reload()
  await expect(page.getByRole("heading", { name: "Categorias" })).toBeVisible()
  await expect(page.getByRole("checkbox", { name: /Tubos/i })).toBeChecked()
})

// ---------------------------------------------------------------------------
// F4 Finance user can view but cannot create
// ---------------------------------------------------------------------------

test("F4 finance user can view but cannot create fornecedor", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")

  await switchUser(page, email, password)
  await page.goto("/fornecedores")
  await expect(
    page.getByRole("heading", { name: /Fornecedores/i }),
  ).toBeVisible()

  // "Novo Fornecedor" button should not be visible
  await expect(
    page.getByRole("button", { name: "Novo Fornecedor" }),
  ).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// F5 Client user does not see Fornecedores in sidebar
// ---------------------------------------------------------------------------

test("F5 client user does not see Fornecedores in sidebar", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "client")

  await switchUser(page, email, password)
  await page.goto("/")

  await expect(
    page.getByRole("link", { name: /Fornecedores/i }),
  ).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// F6 Invalid CNPJ shows validation error
// ---------------------------------------------------------------------------

test("F6 invalid CNPJ shows validation error", async ({ page }) => {
  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto("/fornecedores/new")

  await page.getByLabel(/Nome da Empresa/i).fill("Test CNPJ Invalid")
  // Enter CNPJ with wrong format (lowercase letters — fails frontend regex)
  await page.getByLabel(/^CNPJ$/i).fill("abcdefghij1234")

  await page.getByRole("button", { name: "Criar Fornecedor" }).click()

  // Frontend Zod validation error
  await expect(page.getByText(/CNPJ inválido/i)).toBeVisible()
})

// ---------------------------------------------------------------------------
// F7 Delete fornecedor removes it from list
// ---------------------------------------------------------------------------

test("F7 superuser deletes fornecedor — removed from list", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  const res = await fetch(`${API_BASE}/api/v1/fornecedores`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      company_name: "To Be Deleted Supplier",
      categories: [],
      contatos: [],
    }),
  })
  const fornecedor = (await res.json()) as { id: string }

  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto(`/fornecedores/${fornecedor.id}`)

  await page.getByRole("button", { name: /Excluir Fornecedor/i }).click()

  // Confirm dialog
  await expect(page.getByText("Excluir fornecedor?")).toBeVisible()
  await page.getByRole("button", { name: "Confirmar" }).click()

  await expect(page).toHaveURL(/\/fornecedores$/)
  await expect(page.getByText("To Be Deleted Supplier")).not.toBeVisible()
})
