# Frontend — CLAUDE.md

React 19 + TypeScript + Vite + TanStack Router/Query + Tailwind CSS v4 + shadcn/ui.
See root `CLAUDE.md` for full project context.

## Structure

```
frontend/src/
├── routes/          # TanStack Router pages (file-based routing)
├── components/      # Reusable React components
│   └── ui/          # shadcn/ui primitives (do not edit directly)
├── client/          # AUTO-GENERATED OpenAPI client — never hand-edit
├── hooks/           # Custom React hooks
└── lib/             # Utilities (cn helper, etc.)
```

## Routing

TanStack Router uses file-based routing under `src/routes/`. To add a page:
1. Create a new file: `src/routes/clients/index.tsx` → maps to `/clients`
2. Export a `Route` using `createFileRoute`

## API Calls

- **Never write fetch/axios calls manually**
- Always use the generated client: `import { ClientsService } from "@/client"`
- After any backend API change, regenerate: `bash ../scripts/generate-client.sh`
- Wrap all API calls in TanStack Query (`useQuery`, `useMutation`)

## Component Conventions

- Use shadcn/ui components from `@/components/ui/` for all UI primitives
- Forms use React Hook Form — always validate with Zod schemas
- CPF/CNPJ inputs should format/mask on the fly (use a mask library or custom hook)

## Styling

- Tailwind CSS v4 — utility classes only, no custom CSS unless unavoidable
- Dark mode is supported via the built-in theme provider

## Key Commands

```bash
bun run dev          # start dev server (http://localhost:5173)
bun run build        # production build
bun run lint         # Biome lint + format check
bun run test         # Playwright E2E tests
```

## Package Management

```bash
bun add <package>    # add dependency
bun install          # install all deps
```
