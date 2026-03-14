/**
 * E2E tests for Phase 7 Estoque (Inventory)
 *
 * E1 Superuser can view estoque dashboard
 * E2 Superuser can create a product type and product via API + UI
 * E3 Superuser sees product in the products list
 * E4 Finance user can view estoque but not create
 * E5 Client user does not see Estoque in sidebar
 * E6 Product detail page shows stock history
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
// E1 Superuser can view estoque dashboard
// ---------------------------------------------------------------------------

test("E1 superuser can view estoque dashboard", async ({ page }) => {
  await switchUser(page, firstSuperuser, firstSuperuserPassword)

  await page.goto("/estoque")
  await expect(page.getByRole("heading", { name: /Estoque/i })).toBeVisible()

  // Expect category cards to be present
  await expect(page.getByText("Tubos")).toBeVisible()
  await expect(page.getByText("Conexões")).toBeVisible()
  await expect(page.getByText("Bombas")).toBeVisible()
})

// ---------------------------------------------------------------------------
// E2 Superuser creates a product type and product
// ---------------------------------------------------------------------------

test("E2 superuser creates product type and product via API + navigates to it", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  // Create product type via API
  const ptRes = await fetch(`${API_BASE}/api/v1/product-types`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      category: "tubos",
      name: `Tubo Teste E2E ${Date.now()}`,
      unit_of_measure: "un",
    }),
  })
  const pt = (await ptRes.json()) as { id: string; name: string }
  expect(ptRes.status).toBe(201)

  // Create product via API
  const prodRes = await fetch(`${API_BASE}/api/v1/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      product_type_id: pt.id,
      name: `Produto Teste E2E ${Date.now()}`,
      unit_price: "15.50",
    }),
  })
  const prod = (await prodRes.json()) as { id: string; name: string }
  expect(prodRes.status).toBe(201)

  // Navigate to product detail page
  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto(`/estoque/produtos/${prod.id}`)

  await expect(page.getByText(prod.name)).toBeVisible()
})

// ---------------------------------------------------------------------------
// E3 Superuser sees product in products list
// ---------------------------------------------------------------------------

test("E3 superuser sees product in estoque produtos list", async ({ page }) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  // Create product type and product via API
  const ptRes = await fetch(`${API_BASE}/api/v1/product-types`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      category: "bombas",
      name: `Bomba Teste List ${Date.now()}`,
      unit_of_measure: "un",
    }),
  })
  const pt = (await ptRes.json()) as { id: string }

  const uniqueName = `Bomba Lista E3 ${Date.now()}`
  await fetch(`${API_BASE}/api/v1/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      product_type_id: pt.id,
      name: uniqueName,
      unit_price: "250.00",
    }),
  })

  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto("/estoque/produtos")

  await expect(page.getByRole("heading", { name: /Produtos/i })).toBeVisible()
  await expect(page.getByText(uniqueName)).toBeVisible()

  // "Adicionar Produto" button visible for admin
  await expect(
    page.getByRole("link", { name: /Adicionar Produto/i }),
  ).toBeVisible()
})

// ---------------------------------------------------------------------------
// E4 Finance user can view estoque but not create
// ---------------------------------------------------------------------------

test("E4 finance user can view estoque but not create products", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "finance")

  await switchUser(page, email, password)
  await page.goto("/estoque")

  await expect(page.getByRole("heading", { name: /Estoque/i })).toBeVisible()

  await page.goto("/estoque/produtos")
  await expect(page.getByRole("heading", { name: /Produtos/i })).toBeVisible()

  // "Adicionar Produto" button should NOT be visible for finance user
  await expect(
    page.getByRole("link", { name: /Adicionar Produto/i }),
  ).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// E5 Client user does not see Estoque in sidebar
// ---------------------------------------------------------------------------

test("E5 client user does not see Estoque in sidebar", async ({ page }) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  const { email, password } = await createUserWithRole(superToken, "client")

  await switchUser(page, email, password)
  await page.goto("/")

  await expect(page.getByRole("link", { name: /Estoque/i })).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// E6 Product detail page shows stock history and prediction card
// ---------------------------------------------------------------------------

test("E6 product detail shows prediction card and empty history", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)

  const ptRes = await fetch(`${API_BASE}/api/v1/product-types`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      category: "cabos",
      name: `Cabo Detail Test ${Date.now()}`,
      unit_of_measure: "m",
    }),
  })
  const pt = (await ptRes.json()) as { id: string }

  const prodRes = await fetch(`${API_BASE}/api/v1/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${superToken}`,
    },
    body: JSON.stringify({
      product_type_id: pt.id,
      name: `Cabo Detail E6 ${Date.now()}`,
      unit_price: "5.00",
    }),
  })
  const prod = (await prodRes.json()) as { id: string; name: string }

  await switchUser(page, firstSuperuser, firstSuperuserPassword)
  await page.goto(`/estoque/produtos/${prod.id}`)

  await expect(page.getByText(prod.name)).toBeVisible()
  await expect(page.getByText("Previsão de Estoque")).toBeVisible()
  await expect(page.getByText(/Histórico de Estoque/i)).toBeVisible()
  await expect(page.getByText(/Nenhuma entrada de estoque/i)).toBeVisible()

  // "Adicionar Entrada" button visible for admin
  await expect(
    page.getByRole("button", { name: /Adicionar Entrada/i }),
  ).toBeVisible()
})
