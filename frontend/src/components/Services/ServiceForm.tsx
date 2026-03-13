import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"
import { Plus, Trash2 } from "lucide-react"

import {
  type ServiceCreate,
  type ServiceItemCreate,
  type ServiceType,
  ClientsService,
  ServicesService,
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
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const ITEM_TYPES = ["material", "serviço"] as const
const SERVICE_TYPES = ["perfuração", "reparo"] as const

const itemSchema = z.object({
  item_type: z.enum(ITEM_TYPES, {
    error: "Tipo é obrigatório",
  }),
  description: z.string().min(1, { message: "Descrição é obrigatória" }).max(500),
  quantity: z.number().gt(0, { message: "Quantidade deve ser maior que 0" }),
  unit_price: z.number().gte(0, { message: "Preço não pode ser negativo" }),
})

const formSchema = z.object({
  client_id: z.string().min(1, { message: "Cliente é obrigatório" }),
  type: z.enum(SERVICE_TYPES, {
    error: "Tipo de serviço é obrigatório",
  }),
  execution_address: z
    .string()
    .min(1, { message: "Endereço de execução é obrigatório" })
    .max(500),
  notes: z.string().max(5000).optional().or(z.literal("")),
  items: z.array(itemSchema),
})

type FormData = z.infer<typeof formSchema>

interface ServiceFormProps {
  isOpen: boolean
  onClose: () => void
}

const ServiceForm = ({ isOpen, onClose }: ServiceFormProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: clients } = useQuery({
    queryKey: ["clients"],
    queryFn: () => ClientsService.readClients({ skip: 0, limit: 500 }),
    enabled: isOpen,
  })

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      client_id: "",
      type: "perfuração",
      execution_address: "",
      notes: "",
      items: [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "items",
  })

  const mutation = useMutation({
    mutationFn: async (data: FormData) => {
      const service = await ServicesService.createService({
        requestBody: {
          client_id: data.client_id,
          type: data.type as ServiceType,
          execution_address: data.execution_address,
          notes: data.notes || null,
        } as ServiceCreate,
      })
      for (const item of data.items) {
        await ServicesService.addItem({
          serviceId: service.id,
          requestBody: item as ServiceItemCreate,
        })
      }
      return service
    },
    onSuccess: () => {
      showSuccessToast("Serviço cadastrado com sucesso")
      form.reset()
      onClose()
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  const handleClose = () => {
    form.reset()
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Novo Serviço</DialogTitle>
              <DialogDescription>
                Preencha o formulário abaixo para cadastrar um novo serviço.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="client_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Cliente <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o cliente" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {clients?.data.map((client) => (
                          <SelectItem key={client.id} value={client.id}>
                            {client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Tipo <span className="text-destructive">*</span>
                      </FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="perfuração">Perfuração</SelectItem>
                          <SelectItem value="reparo">Reparo</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="execution_address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Endereço de Execução <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Endereço completo onde o serviço será executado" {...field} />
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
                        placeholder="Observações adicionais sobre o serviço"
                        className="resize-none"
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <FormLabel>Itens do Serviço</FormLabel>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      append({
                        item_type: "material",
                        description: "",
                        quantity: 1,
                        unit_price: 0,
                      })
                    }
                  >
                    <Plus className="mr-1 h-3 w-3" />
                    Adicionar Item
                  </Button>
                </div>

                {fields.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">
                    Nenhum item adicionado.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {fields.map((field, index) => (
                      <div
                        key={field.id}
                        className="grid grid-cols-12 gap-2 items-start border rounded-md p-3"
                      >
                        <div className="col-span-2">
                          <FormField
                            control={form.control}
                            name={`items.${index}.item_type`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-xs">Tipo</FormLabel>
                                <Select value={field.value} onValueChange={field.onChange}>
                                  <FormControl>
                                    <SelectTrigger className="h-8 text-xs">
                                      <SelectValue />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    <SelectItem value="material">Material</SelectItem>
                                    <SelectItem value="serviço">Serviço</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className="col-span-4">
                          <FormField
                            control={form.control}
                            name={`items.${index}.description`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-xs">Descrição</FormLabel>
                                <FormControl>
                                  <Input className="h-8 text-xs" placeholder="Descrição" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className="col-span-2">
                          <FormField
                            control={form.control}
                            name={`items.${index}.quantity`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-xs">Qtd</FormLabel>
                                <FormControl>
                                  <Input
                                    className="h-8 text-xs"
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    {...field}
                                    onChange={(e) => field.onChange(e.target.valueAsNumber)}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className="col-span-3">
                          <FormField
                            control={form.control}
                            name={`items.${index}.unit_price`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-xs">Preço Unit.</FormLabel>
                                <FormControl>
                                  <Input
                                    className="h-8 text-xs"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    {...field}
                                    onChange={(e) => field.onChange(e.target.valueAsNumber)}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className="col-span-1 flex items-end pb-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending} onClick={handleClose}>
                  Cancelar
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Cadastrar
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default ServiceForm
