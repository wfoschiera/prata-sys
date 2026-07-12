/**
 * E2E tests for Clientes (Clients) — /clients
 *
 * C1 Superuser creates a client via the ClientForm — appears in the list
 * C2 Superuser edits a client — updated name is shown
 * C3 Superuser deletes a client — disappears from the list
 * C4 Client-role user is redirected away from /clients (route guard)
 */
import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

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
  const name = uniqueName("Cliente E2E")
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

// ---------------------------------------------------------------------------
// C1 create client via the UI form
// ---------------------------------------------------------------------------

test("C1 superuser creates a client and sees it in the list", async ({
  page,
}) => {
  const name = uniqueName("Cliente Novo")
  const cpf = randomCpf()

  await page.goto("/clients")
  await expect(page.getByRole("heading", { name: "Clientes" })).toBeVisible()

  await page.getByRole("button", { name: "Adicionar Cliente" }).click()
  await expect(page.getByRole("dialog")).toBeVisible()

  // Default document_type is "cpf" so the number placeholder is "11 dígitos".
  await page.getByPlaceholder("Nome completo ou razão social").fill(name)
  await page.getByPlaceholder("11 dígitos").fill(cpf)
  await page.getByRole("button", { name: "Cadastrar" }).click()

  await expect(page.getByText("Cliente cadastrado com sucesso")).toBeVisible()
  await expect(page.getByRole("dialog")).not.toBeVisible()

  // NOTE: crud.get_clients has no explicit ORDER BY, so on a DB with >20
  // clients the new row could land on a later page. The success toast above
  // is the definitive proof of creation; the list assertion assumes the E2E
  // DB stays small enough for the row to appear on page 1.
  await expect(page.getByRole("row").filter({ hasText: name })).toBeVisible()
})

// ---------------------------------------------------------------------------
// C2 edit an existing client
// ---------------------------------------------------------------------------

test("C2 superuser edits a client and sees the updated name", async ({
  page,
}) => {
  const token = await getToken(firstSuperuser, firstSuperuserPassword)
  const { name } = await createClientViaApi(token)
  const updatedName = uniqueName("Cliente Editado")

  await page.goto("/clients")
  const row = page.getByRole("row").filter({ hasText: name })
  await expect(row).toBeVisible()

  await row.getByRole("button", { name: "Editar cliente" }).click()
  await expect(
    page.getByRole("heading", { name: "Editar Cliente" }),
  ).toBeVisible()

  await page.getByPlaceholder("Nome completo ou razão social").fill(updatedName)
  await page.getByRole("button", { name: "Salvar" }).click()

  await expect(page.getByText("Cliente atualizado com sucesso")).toBeVisible()
  await expect(page.getByRole("dialog")).not.toBeVisible()
  await expect(
    page.getByRole("row").filter({ hasText: updatedName }),
  ).toBeVisible()
})

// ---------------------------------------------------------------------------
// C3 delete a client
// ---------------------------------------------------------------------------

test("C3 superuser deletes a client and it disappears from the list", async ({
  page,
}) => {
  const token = await getToken(firstSuperuser, firstSuperuserPassword)
  const { name } = await createClientViaApi(token)

  await page.goto("/clients")
  const row = page.getByRole("row").filter({ hasText: name })
  await expect(row).toBeVisible()

  await row.getByRole("button", { name: "Excluir cliente" }).click()

  const dialog = page.getByRole("dialog")
  await expect(
    dialog.getByRole("heading", { name: "Excluir Cliente" }),
  ).toBeVisible()
  await dialog.getByRole("button", { name: "Excluir" }).click()

  await expect(page.getByText("Cliente excluído com sucesso")).toBeVisible()
  await expect(
    page.getByRole("row").filter({ hasText: name }),
  ).not.toBeVisible()
})

// ---------------------------------------------------------------------------
// C4 client-role user cannot access /clients (route guard redirects to /)
// ---------------------------------------------------------------------------

test.describe("Clients page access control", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("C4 client-role user is redirected away from /clients", async ({
    page,
  }) => {
    const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
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
        full_name: "Test client user",
        is_verified: true,
        role: "client",
      }),
    })

    await logInUser(page, email, password)
    await page.goto("/clients")

    // beforeLoad redirects role=client to "/"
    await expect(
      page.getByRole("heading", { name: "Clientes" }),
    ).not.toBeVisible()
    await expect(page).not.toHaveURL(/\/clients/)
  })
})
