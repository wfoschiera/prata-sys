/**
 * Brand identity for the application.
 *
 * Single source of truth for the app name shown in the UI (page titles,
 * footer, logo wordmark). Change it here to rebrand everywhere on the frontend.
 * The backend has its own equivalent placeholder: `settings.PROJECT_NAME`.
 */
export const APP_NAME = "Prata Poços"

/**
 * Build a document title for a page, suffixed with the app name.
 * e.g. `pageTitle("Clientes")` -> "Clientes - Prata Poços".
 */
export function pageTitle(section: string): string {
  return `${section} - ${APP_NAME}`
}
