import type { APIRequestContext } from "@playwright/test"

// Mailpit JSON message shape (subset we use).
// See: https://mailpit.axllent.org/docs/api-v1/
export type MailpitMessage = {
  ID: string
  To: { Address: string; Name?: string }[]
  Subject: string
}

type MailpitListResponse = {
  messages: MailpitMessage[]
}

async function findEmail({
  request,
  filter,
}: {
  request: APIRequestContext
  filter?: (email: MailpitMessage) => boolean
}) {
  const response = await request.get(`${process.env.MAILPIT_HOST}/api/v1/messages`)
  const data = (await response.json()) as MailpitListResponse

  let messages = data.messages ?? []
  if (filter) {
    messages = messages.filter(filter)
  }

  // Mailpit returns newest first, so the most recent matching email is at index 0.
  const email = messages[0]
  return email ?? null
}

export function findLastEmail({
  request,
  filter,
  timeout = 5000,
}: {
  request: APIRequestContext
  filter?: (email: MailpitMessage) => boolean
  timeout?: number
}) {
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(
      () => reject(new Error("Timeout while trying to get latest email")),
      timeout,
    ),
  )

  const checkEmails = async () => {
    while (true) {
      const emailData = await findEmail({ request, filter })
      if (emailData) {
        return emailData
      }
      await new Promise((resolve) => setTimeout(resolve, 100))
    }
  }

  return Promise.race([timeoutPromise, checkEmails()])
}
