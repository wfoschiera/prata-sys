import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  type CategoriaTransacao,
  type TransacaoPublic,
  TransacoesService,
} from "@/client"
import { Badge } from "@/components/ui/badge"
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
  categoria: z.string().min(1, { message: "Selecione a categoria" }),
  valor: z
    .number({ error: "Informe o valor" })
    .positive({ message: "Valor deve ser positivo" }),
  data_competencia: z.string().min(1, { message: "Informe a data" }),
  nome_contraparte: z.string().optional(),
  descricao: z.string().optional(),
  service_id: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface EditTransacaoProps {
  transacao: TransacaoPublic
  onSuccess: () => void
}

const EditTransacao = ({ transacao, onSuccess }: EditTransacaoProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const categorias =
    transacao.tipo === "receita" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      categoria: transacao.categoria,
      valor: parseFloat(transacao.valor),
      data_competencia: transacao.data_competencia,
      nome_contraparte: transacao.nome_contraparte ?? "",
      descricao: transacao.descricao ?? "",
      service_id: transacao.service_id ?? "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      TransacoesService.updateTransacao({
        transacaoId: transacao.id,
        requestBody: {
          categoria: data.categoria as CategoriaTransacao,
          valor: data.valor,
          data_competencia: data.data_competencia,
          descricao: data.descricao || null,
          nome_contraparte: data.nome_contraparte || null,
          service_id: data.service_id || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Transação atualizada com sucesso")
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

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon">
          <Pencil className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Editar Transação</DialogTitle>
          <DialogDescription>
            Atualize os dados da transação. O tipo não pode ser alterado.
          </DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2 pb-2">
          <span className="text-sm text-muted-foreground">Tipo:</span>
          <Badge
            variant={transacao.tipo === "receita" ? "default" : "destructive"}
          >
            {transacao.tipo === "receita" ? "Receita" : "Despesa"}
          </Badge>
        </div>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-2">
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
                        {categorias.map((cat) => (
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

export default EditTransacao
