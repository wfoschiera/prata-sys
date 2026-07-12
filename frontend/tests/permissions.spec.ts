/**
 * E2E tests for the Permissions matrix — /permissions
 *
 * P1 Matrix loads (heading, "Usuário" column, superuser row rendered)
 * P2 Toggling a permission override for a user persists across a reload
 */
import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomEmail, randomPassword } from "./utils/random"

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

async function createUserViaApi(
  superToken: string,
  role: "finance" | "admin" | "client",
): Promise<{ email: string }> {
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
      // Include the email in full_name so the matrix row (which renders
      // full_name || email) can be located by the unique email string.
      full_name: `Perm Test ${role} ${email}`,
      is_verified: true,
      role,
    }),
  })
  return { email }
}

// ---------------------------------------------------------------------------
// P1 matrix loads
// ---------------------------------------------------------------------------

test("P1 permissions matrix loads with users", async ({ page }) => {
  await page.goto("/permissions")

  await expect(page.getByRole("heading", { name: "Permissões" })).toBeVisible()
  // Exact match: "Usuário" would otherwise also match the "Gerenciar Usuários"
  // permission column header.
  await expect(
    page.getByRole("columnheader", { name: "Usuário", exact: true }),
  ).toBeVisible()
  // Exactly one superuser row is present in the matrix (labelled superusuário).
  await expect(page.getByText("superusuário")).toBeVisible()
})

// ---------------------------------------------------------------------------
// P2 toggling an override persists across reload
// ---------------------------------------------------------------------------

test("P2 toggling a permission override persists after reload", async ({
  page,
}) => {
  const superToken = await getToken(firstSuperuser, firstSuperuserPassword)
  // A client-role user has few role defaults, so its row has enabled
  // (togglable) checkboxes for non-default permissions.
  const { email } = await createUserViaApi(superToken, "client")

  await page.goto("/permissions")

  const row = page.getByRole("row").filter({ hasText: email })
  await expect(row).toBeVisible()

  // Enabled checkboxes are overridable permissions (superuser + role-default
  // cells are rendered disabled). Radix Checkbox is a <button role="checkbox">.
  const enabledBoxes = row.locator('[role="checkbox"]:not([disabled])')
  const target = enabledBoxes.first()
  await expect(target).toBeVisible()
  await expect(target).not.toBeChecked()

  await target.click()
  await expect(page.getByText("Permissões atualizadas")).toBeVisible()

  // Reload and confirm the override was persisted (still enabled + now checked)
  await page.reload()
  const rowAfter = page.getByRole("row").filter({ hasText: email })
  await expect(
    rowAfter.locator('[role="checkbox"]:not([disabled])').first(),
  ).toBeChecked()
})
