import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createFileRoute,
  redirect,
  useNavigate,
  useParams,
} from "@tanstack/react-router"
import { ArrowLeft, Pencil, Plus, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type FornecedorCategoryEnum,
  type FornecedorContatoPublic,
  FornecedoresService,
  UsersService,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/fornecedores/$fornecedorId")({
  component: FornecedorDetail,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (
      !user.is_superuser &&
      !user.permissions?.includes("view_fornecedores")
    ) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Fornecedor - Prata Sys" }],
  }),
})

// ── Constants ──────────────────────────────────────────────────────────────────

const ALL_CATEGORIES: FornecedorCategoryEnum[] = [
  "tubos",
  "conexoes",
  "bombas",
  "cabos",
  "outros",
]
const CATEGORY_LABELS: Record<FornecedorCategoryEnum, string> = {
  tubos: "Tubos",
  conexoes: "Conexões",
  bombas: "Bombas",
  cabos: "Cabos",
  outros: "Outros",
}

// ── Zod schemas ────────────────────────────────────────────────────────────────

const companySchema = z.object({
  company_name: z.string().min(1, "Nome obrigatório"),
  cnpj: z
    .string()
    .regex(/^[A-Z0-9]{12}\d{2}$/, "CNPJ inválido (14 caracteres alfanuméricos)")
    .optional()
    .or(z.literal("")),
  address: z.string().optional(),
  notes: z.string().optional(),
})

const contatoSchema = z.object({
  name: z.string().min(1, "Nome obrigatório"),
  telefone: z.string().min(1, "Telefone obrigatório"),
  whatsapp: z.string().optional(),
  description: z.string().min(1, "Descrição obrigatória"),
})

type CompanyFormValues = z.infer<typeof companySchema>
type ContatoFormValues = z.infer<typeof contatoSchema>

// ── Contato form dialog ────────────────────────────────────────────────────────

interface ContatoDialogProps {
  fornecedorId: string
  contato?: FornecedorContatoPublic
  isOpen: boolean
  onClose: () => void
}

function ContatoDialog({
  fornecedorId,
  contato,
  isOpen,
  onClose,
}: ContatoDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<ContatoFormValues>({
    resolver: zodResolver(contatoSchema),
    defaultValues: {
      name: contato?.name ?? "",
      telefone: contato?.telefone ?? "",
      whatsapp: contato?.whatsapp ?? "",
      description: contato?.description ?? "",
    },
  })

  useEffect(() => {
    form.reset({
      name: contato?.name ?? "",
      telefone: contato?.telefone ?? "",
      whatsapp: contato?.whatsapp ?? "",
      description: contato?.description ?? "",
    })
  }, [contato, form])

  const mutation = useMutation({
    mutationFn: (values: ContatoFormValues) =>
      contato
        ? FornecedoresService.updateContato({
            fornecedorId,
            contatoId: contato.id,
            requestBody: {
              name: values.name,
              telefone: values.telefone,
              whatsapp: values.whatsapp || undefined,
              description: values.description,
            },
          })
        : FornecedoresService.createContato({
            fornecedorId,
            requestBody: {
              name: values.name,
              telefone: values.telefone,
              whatsapp: values.whatsapp || undefined,
              description: values.description,
            },
          }),
    onSuccess: () => {
      showSuccessToast(contato ? "Contato atualizado" : "Contato adicionado")
      queryClient.invalidateQueries({
        queryKey: ["fornecedores", fornecedorId],
      })
      onClose()
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => !open && !mutation.isPending && onClose()}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {contato ? "Editar Contato" : "Adicionar Contato"}
          </DialogTitle>
          <DialogDescription>
            Preencha as informações do contato.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={mutation.isPending} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Cargo / Função</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={mutation.isPending} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="telefone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Telefone</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={mutation.isPending} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="whatsapp"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>WhatsApp (opcional)</FormLabel>
                  <FormControl>
                    <Input {...field} disabled={mutation.isPending} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={mutation.isPending}
              >
                Cancelar
              </Button>
              <LoadingButton type="submit" loading={mutation.isPending}>
                {contato ? "Salvar" : "Adicionar"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

// ── Delete confirmation dialog ─────────────────────────────────────────────────

interface DeleteDialogProps {
  title: string
  description: string
  isOpen: boolean
  isPending: boolean
  onConfirm: () => void
  onClose: () => void
}

function DeleteDialog({
  title,
  description,
  isOpen,
  isPending,
  onConfirm,
  onClose,
}: DeleteDialogProps) {
  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => !open && !isPending && onClose()}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <LoadingButton
            variant="destructive"
            onClick={onConfirm}
            loading={isPending}
          >
            Confirmar
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

function FornecedorDetail() {
  const { fornecedorId } = useParams({
    from: "/_layout/fornecedores/$fornecedorId",
  })
  const isNew = fornecedorId === "new"
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user: currentUser } = useAuth()
  const canManage =
    currentUser?.is_superuser ||
    currentUser?.permissions?.includes("manage_fornecedores")

  const [contatoDialogOpen, setContatoDialogOpen] = useState(false)
  const [editContato, setEditContato] = useState<
    FornecedorContatoPublic | undefined
  >(undefined)
  const [deleteContatoId, setDeleteContatoId] = useState<string | null>(null)
  const [deleteFornecedorOpen, setDeleteFornecedorOpen] = useState(false)

  const { data: fornecedor, isLoading } = useQuery({
    queryKey: ["fornecedores", fornecedorId],
    queryFn: () => FornecedoresService.getFornecedor({ fornecedorId }),
    enabled: !isNew,
  })

  // Company form
  const form = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      company_name: "",
      cnpj: "",
      address: "",
      notes: "",
    },
  })

  useEffect(() => {
    if (fornecedor) {
      form.reset({
        company_name: fornecedor.company_name,
        cnpj: fornecedor.cnpj ?? "",
        address: fornecedor.address ?? "",
        notes: fornecedor.notes ?? "",
      })
    }
  }, [fornecedor, form])

  const saveMutation = useMutation({
    mutationFn: (values: CompanyFormValues) => {
      const payload = {
        company_name: values.company_name,
        cnpj: values.cnpj || null,
        address: values.address || null,
        notes: values.notes || null,
      }
      return isNew
        ? FornecedoresService.createFornecedor({ requestBody: payload })
        : FornecedoresService.updateFornecedor({
            fornecedorId,
            requestBody: payload,
          })
    },
    onSuccess: (data) => {
      showSuccessToast(isNew ? "Fornecedor criado" : "Fornecedor atualizado")
      queryClient.invalidateQueries({ queryKey: ["fornecedores"] })
      if (isNew) {
        navigate({
          to: "/fornecedores/$fornecedorId",
          params: { fornecedorId: data.id },
        })
      }
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  // Category toggle
  const categoryMutation = useMutation({
    mutationFn: (categories: FornecedorCategoryEnum[]) =>
      FornecedoresService.updateFornecedor({
        fornecedorId,
        requestBody: { categories },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["fornecedores", fornecedorId],
      })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const toggleCategory = (cat: FornecedorCategoryEnum) => {
    if (!fornecedor) return
    const current = fornecedor.categories
    const next = current.includes(cat)
      ? current.filter((c) => c !== cat)
      : [...current, cat]
    categoryMutation.mutate(next)
  }

  // Delete contato
  const deleteContatoMutation = useMutation({
    mutationFn: (contatoId: string) =>
      FornecedoresService.deleteContato({ fornecedorId, contatoId }),
    onSuccess: () => {
      showSuccessToast("Contato removido")
      queryClient.invalidateQueries({
        queryKey: ["fornecedores", fornecedorId],
      })
      setDeleteContatoId(null)
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  // Delete fornecedor
  const deleteFornecedorMutation = useMutation({
    mutationFn: () => FornecedoresService.deleteFornecedor({ fornecedorId }),
    onSuccess: () => {
      showSuccessToast("Fornecedor excluído")
      queryClient.invalidateQueries({ queryKey: ["fornecedores"] })
      navigate({ to: "/fornecedores" })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  if (!isNew && isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate({ to: "/fornecedores" })}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {isNew
              ? "Novo Fornecedor"
              : (fornecedor?.company_name ?? "Fornecedor")}
          </h1>
          <p className="text-muted-foreground text-sm">
            {isNew
              ? "Preencha os dados da empresa"
              : "Edite os dados do fornecedor"}
          </p>
        </div>
      </div>

      {/* Section 1: Company data */}
      <section className="rounded-lg border p-6 space-y-4">
        <h2 className="font-semibold text-lg">Dados da Empresa</h2>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="company_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome da Empresa *</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      disabled={!canManage || saveMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="cnpj"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>CNPJ</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="14 dígitos alfanuméricos"
                      disabled={!canManage || saveMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Endereço</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      disabled={!canManage || saveMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Observações</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      rows={3}
                      disabled={!canManage || saveMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {canManage && (
              <div className="flex justify-end">
                <LoadingButton type="submit" loading={saveMutation.isPending}>
                  {isNew ? "Criar Fornecedor" : "Salvar Alterações"}
                </LoadingButton>
              </div>
            )}
          </form>
        </Form>
      </section>

      {/* Section 2: Categories (only for existing) */}
      {!isNew && fornecedor && (
        <section className="rounded-lg border p-6 space-y-4">
          <h2 className="font-semibold text-lg">Categorias</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {ALL_CATEGORIES.map((cat) => (
              <div key={cat} className="flex items-center gap-2">
                <Checkbox
                  id={`cat-${cat}`}
                  checked={fornecedor.categories.includes(cat)}
                  onCheckedChange={() => canManage && toggleCategory(cat)}
                  disabled={!canManage || categoryMutation.isPending}
                />
                <Label htmlFor={`cat-${cat}`} className="cursor-pointer">
                  {CATEGORY_LABELS[cat]}
                </Label>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Section 3: Contacts (only for existing) */}
      {!isNew && fornecedor && (
        <section className="rounded-lg border p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg">Contatos</h2>
            {canManage && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditContato(undefined)
                  setContatoDialogOpen(true)
                }}
              >
                <Plus className="mr-1 h-3 w-3" />
                Adicionar
              </Button>
            )}
          </div>
          {fornecedor.contatos.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nenhum contato cadastrado.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Função</TableHead>
                  <TableHead>Telefone</TableHead>
                  <TableHead>WhatsApp</TableHead>
                  {canManage && (
                    <TableHead>
                      <span className="sr-only">Ações</span>
                    </TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {fornecedor.contatos.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {c.description}
                    </TableCell>
                    <TableCell>{c.telefone}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {c.whatsapp ?? "—"}
                    </TableCell>
                    {canManage && (
                      <TableCell>
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setEditContato(c)
                              setContatoDialogOpen(true)
                            }}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setDeleteContatoId(c.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </section>
      )}

      {/* Delete fornecedor */}
      {!isNew && canManage && (
        <div className="border-t pt-4">
          <Button
            variant="destructive"
            onClick={() => setDeleteFornecedorOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Excluir Fornecedor
          </Button>
        </div>
      )}

      {/* Dialogs */}
      {!isNew && fornecedor && (
        <>
          <ContatoDialog
            fornecedorId={fornecedorId}
            contato={editContato}
            isOpen={contatoDialogOpen}
            onClose={() => {
              setContatoDialogOpen(false)
              setEditContato(undefined)
            }}
          />

          <DeleteDialog
            title="Remover contato?"
            description="Esta ação não pode ser desfeita."
            isOpen={!!deleteContatoId}
            isPending={deleteContatoMutation.isPending}
            onConfirm={() =>
              deleteContatoId && deleteContatoMutation.mutate(deleteContatoId)
            }
            onClose={() => setDeleteContatoId(null)}
          />

          <DeleteDialog
            title="Excluir fornecedor?"
            description="Todos os contatos serão removidos junto com o fornecedor. Esta ação não pode ser desfeita."
            isOpen={deleteFornecedorOpen}
            isPending={deleteFornecedorMutation.isPending}
            onConfirm={() => deleteFornecedorMutation.mutate()}
            onClose={() => setDeleteFornecedorOpen(false)}
          />
        </>
      )}
    </div>
  )
}
