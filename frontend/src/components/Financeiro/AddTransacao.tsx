import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type CategoriaTransacao,
  type TipoTransacao,
  TransacoesService,
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
  DialogTrigger,
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
import {
  CATEGORIA_LABELS,
  EXPENSE_CATEGORIES,
  INCOME_CATEGORIES,
} from "./constants"

const formSchema = z.object({
  tipo: z.enum(["receita", "despesa"], { error: "Selecione o tipo" }),
  categoria: z.string().min(1, { message: "Selecione a categoria" }),
  valor: z
    .number({ error: "Informe o valor" })
    .positive({ message: "Valor deve ser positivo" }),
  data_competencia: z.string().min(1, { message: "Informe a data" }),
  nome_contraparte: z.string().optional(),
  descricao: z.string().optional(),
  service_id: z.string().optional(),
  client_id: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface AddTransacaoProps {
  onSuccess: () => void
  tipoFixo?: TipoTransacao
}

const today = new Date().toISOString().split("T")[0]

const AddTransacao = ({ onSuccess, tipoFixo }: AddTransacaoProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      tipo: tipoFixo ?? "receita",
      categoria: "",
      valor: undefined,
      data_competencia: today,
      nome_contraparte: "",
      descricao: "",
      service_id: "",
      client_id: "",
    },
  })

  const tipoWatched = form.watch("tipo")
  const categoriasDisponiveis =
    tipoWatched === "receita" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      TransacoesService.createTransacao({
        requestBody: {
          tipo: data.tipo as TipoTransacao,
          categoria: data.categoria as CategoriaTransacao,
          valor: data.valor,
          data_competencia: data.data_competencia,
          descricao: data.descricao || null,
          nome_contraparte: data.nome_contraparte || null,
          service_id: data.service_id || null,
          client_id: data.client_id || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Transação criada com sucesso")
      form.reset()
      setIsOpen(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["transacoes"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  const buttonLabel =
    tipoFixo === "despesa"
      ? "Nova Despesa"
      : tipoFixo === "receita"
        ? "Nova Receita"
        : "Nova Transação"

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {buttonLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{buttonLabel}</DialogTitle>
          <DialogDescription>
            Preencha os dados da transação financeira.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="tipo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Tipo <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={(val) => {
                        field.onChange(val)
                        form.setValue("categoria", "")
                      }}
                      value={field.value}
                      disabled={!!tipoFixo}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o tipo" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="receita">Receita</SelectItem>
                        <SelectItem value="despesa">Despesa</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="categoria"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Categoria <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione a categoria" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {categoriasDisponiveis.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {CATEGORIA_LABELS[cat]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="valor"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Valor (R$) <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="0,00"
                        value={field.value ?? ""}
                        onChange={(e) => field.onChange(e.target.valueAsNumber)}
                        onBlur={field.onBlur}
                        name={field.name}
                        ref={field.ref}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="data_competencia"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Data de Competência{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="nome_contraparte"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Contraparte</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Nome do cliente, fornecedor, etc."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {tipoWatched === "receita" && (
                <FormField
                  control={form.control}
                  name="client_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>ID do Cliente</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="UUID do cliente (opcional)"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="service_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>ID do Serviço</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="UUID do serviço (opcional)"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="descricao"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Descrição</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Observações adicionais..."
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancelar
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Salvar
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddTransacao
