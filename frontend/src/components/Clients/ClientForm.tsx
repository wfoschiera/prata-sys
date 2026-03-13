import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type ClientCreate,
  type ClientPublic,
  ClientsService,
  type ClientUpdate,
  type DocumentType,
} from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
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
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z
  .object({
    name: z.string().min(1, { message: "Nome é obrigatório" }).max(255),
    document_type: z.enum(["cpf", "cnpj"], {
      error: "Tipo de documento é obrigatório",
    }),
    document_number: z
      .string()
      .min(1, { message: "Número do documento é obrigatório" })
      .regex(/^\d+$/, { message: "Apenas dígitos são permitidos" }),
    email: z
      .string()
      .email({ message: "Email inválido" })
      .optional()
      .or(z.literal("")),
    phone: z.string().max(50).optional().or(z.literal("")),
    address: z.string().max(500).optional().or(z.literal("")),
  })
  .superRefine((data, ctx) => {
    if (data.document_type === "cpf" && data.document_number.length !== 11) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "CPF deve ter exatamente 11 dígitos",
        path: ["document_number"],
      })
    }
    if (data.document_type === "cnpj" && data.document_number.length !== 14) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "CNPJ deve ter exatamente 14 dígitos",
        path: ["document_number"],
      })
    }
  })

type FormData = z.infer<typeof formSchema>

interface ClientFormProps {
  isOpen: boolean
  onClose: () => void
  client?: ClientPublic
}

const ClientForm = ({ isOpen, onClose, client }: ClientFormProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEditMode = !!client

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: "",
      document_type: "cpf",
      document_number: "",
      email: "",
      phone: "",
      address: "",
    },
  })

  useEffect(() => {
    if (client) {
      form.reset({
        name: client.name,
        document_type: client.document_type as DocumentType,
        document_number: client.document_number,
        email: client.email ?? "",
        phone: client.phone ?? "",
        address: client.address ?? "",
      })
    } else {
      form.reset({
        name: "",
        document_type: "cpf",
        document_number: "",
        email: "",
        phone: "",
        address: "",
      })
    }
  }, [client, form])

  const createMutation = useMutation({
    mutationFn: (data: ClientCreate) =>
      ClientsService.createClient({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Cliente cadastrado com sucesso")
      onClose()
    },
    onError: (err: any) => {
      if (err?.status === 409) {
        form.setError("document_number", {
          message: "Número de documento já cadastrado",
        })
      } else {
        handleError.call(showErrorToast, err)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: ClientUpdate) =>
      ClientsService.updateClient({ clientId: client!.id, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Cliente atualizado com sucesso")
      onClose()
    },
    onError: (err: any) => {
      if (err?.status === 409) {
        form.setError("document_number", {
          message: "Número de documento já cadastrado",
        })
      } else {
        handleError.call(showErrorToast, err)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] })
    },
  })

  const isPending = createMutation.isPending || updateMutation.isPending

  const onSubmit = (data: FormData) => {
    const payload = {
      name: data.name,
      document_type: data.document_type,
      document_number: data.document_number,
      email: data.email || null,
      phone: data.phone || null,
      address: data.address || null,
    }
    if (isEditMode) {
      updateMutation.mutate(payload)
    } else {
      createMutation.mutate(payload as ClientCreate)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>
                {isEditMode ? "Editar Cliente" : "Adicionar Cliente"}
              </DialogTitle>
              <DialogDescription>
                {isEditMode
                  ? "Atualize os dados do cliente abaixo."
                  : "Preencha o formulário abaixo para cadastrar um novo cliente."}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Nome <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Nome completo ou razão social"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="document_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Tipo <span className="text-destructive">*</span>
                      </FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={(val) => {
                          field.onChange(val)
                          form.trigger("document_number")
                        }}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="cpf">CPF</SelectItem>
                          <SelectItem value="cnpj">CNPJ</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="document_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Número <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder={
                            form.watch("document_type") === "cnpj"
                              ? "14 dígitos"
                              : "11 dígitos"
                          }
                          {...field}
                          maxLength={14}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="email@exemplo.com"
                        type="email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Telefone</FormLabel>
                    <FormControl>
                      <Input placeholder="(00) 00000-0000" {...field} />
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
                      <Input placeholder="Endereço completo" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button
                  variant="outline"
                  disabled={isPending}
                  onClick={onClose}
                >
                  Cancelar
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={isPending}>
                {isEditMode ? "Salvar" : "Cadastrar"}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default ClientForm
