/**
 * E2E tests for Phase 6 Fornecedores (Suppliers)
 *
 * F1 Superuser creates a fornecedor — appears in list
 * F2 Superuser adds a contact to a fornecedor
 * F3 Superuser edits a fornecedor's categories
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

  await page.getByLabel(/Razão Social/i).fill("Empresa Teste Ltda")
  await page.getByRole("button", { name: "Salvar" }).click()

  await expect(page.getByText("Fornecedor salvo")).toBeVisible()
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

  await page.getByRole("button", { name: /Adicionar Contato/i }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  await page.getByLabel(/Nome/i).fill("João Silva")
  await page.getByLabel(/Telefone/i).fill("11999999999")
  await page.getByLabel(/Cargo/i).fill("Gerente")
  await page.getByRole("button", { name: "Salvar" }).click()

  await expect(page.getByRole("dialog")).not.toBeVisible()
  await expect(page.getByText("João Silva")).toBeVisible()
})

// ---------------------------------------------------------------------------
// F3 Superuser edits a fornecedor's categories
// ---------------------------------------------------------------------------

test("F3 superuser sets categories on fornecedor", async ({ page }) => {
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

  // Check a category checkbox
  await page.getByRole("checkbox", { name: /Materiais/i }).check()

  // Save
  await page.getByRole("button", { name: "Salvar" }).click()
  await expect(page.getByText("Fornecedor salvo")).toBeVisible()

  // Reload and verify category is still checked
  await page.reload()
  await expect(page.getByRole("checkbox", { name: /Materiais/i })).toBeChecked()
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

  await page.getByLabel(/Razão Social/i).fill("Test CNPJ Invalid")
  await page.getByLabel(/CNPJ/i).fill("00000000000000")

  await page.getByRole("button", { name: "Salvar" }).click()

  // Should see a validation error (either frontend Zod or backend 422)
  const error = page.getByText(/CNPJ/i)
  await expect(error).toBeVisible()
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
  await expect(page.getByRole("dialog", { name: /Excluir/i })).toBeVisible()
  await page.getByRole("button", { name: /Confirmar/i }).click()

  await expect(page).toHaveURL(/\/fornecedores$/)
  await expect(page.getByText("To Be Deleted Supplier")).not.toBeVisible()
})
