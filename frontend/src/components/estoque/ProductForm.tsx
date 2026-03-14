/**
 * Shared form component for creating and editing a Product.
 * Used by /estoque/produtos/new and /estoque/produtos/$productId/edit.
 */
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  FornecedoresService,
  ProductItemsService,
  type ProductRead,
  ProductsService,
  ProductTypesService,
} from "@/client"
import { Button } from "@/components/ui/button"
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

const productSchema = z.object({
  product_type_id: z
    .string({ error: "Tipo de produto é obrigatório" })
    .min(1, "Tipo de produto é obrigatório"),
  name: z.string({ error: "Nome é obrigatório" }).min(1, "Nome é obrigatório"),
  fornecedor_id: z.string().optional(),
  unit_price: z
    .number({ error: "Preço deve ser um número" })
    .min(0, "Preço deve ser ≥ 0"),
  description: z.string().optional(),
  initial_stock: z.number().min(0, "Quantidade deve ser ≥ 0").optional(),
})

type ProductFormData = z.infer<typeof productSchema>

interface ProductFormProps {
  /** Existing product when editing; undefined when creating */
  product?: ProductRead
}

export function ProductForm({ product }: ProductFormProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const isEditing = !!product

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      product_type_id: product?.product_type_id ?? "",
      name: product?.name ?? "",
      fornecedor_id: product?.fornecedor_id ?? undefined,
      unit_price: product ? Number(product.unit_price) : 0,
      description: product?.description ?? "",
      initial_stock: undefined,
    },
  })

  const { data: productTypes } = useQuery({
    queryKey: ["product-types"],
    queryFn: () => ProductTypesService.listProductTypes(),
  })

  const { data: fornecedores } = useQuery({
    queryKey: ["fornecedores"],
    queryFn: () => FornecedoresService.listFornecedores({}),
  })

  const createMutation = useMutation({
    mutationFn: async (values: ProductFormData) => {
      const created = await ProductsService.createProduct({
        requestBody: {
          product_type_id: values.product_type_id,
          name: values.name,
          fornecedor_id: values.fornecedor_id || null,
          unit_price: values.unit_price,
          description: values.description || null,
        },
      })
      if (values.initial_stock && values.initial_stock > 0) {
        await ProductItemsService.createProductItem({
          requestBody: {
            product_id: created.id,
            quantity: values.initial_stock,
          },
        })
      }
      return created
    },
    onSuccess: (created) => {
      showSuccessToast("Produto criado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["products"] })
      queryClient.invalidateQueries({ queryKey: ["estoque", "dashboard"] })
      void navigate({
        to: "/estoque/produtos/$productId",
        params: { productId: created.id },
      })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const editMutation = useMutation({
    mutationFn: (values: ProductFormData) =>
      ProductsService.updateProduct({
        productId: product!.id,
        requestBody: {
          product_type_id: values.product_type_id || null,
          name: values.name || null,
          fornecedor_id: values.fornecedor_id || null,
          unit_price: values.unit_price,
          description: values.description || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Produto atualizado com sucesso")
      queryClient.invalidateQueries({ queryKey: ["products"] })
      queryClient.invalidateQueries({ queryKey: ["estoque", "dashboard"] })
      void navigate({
        to: "/estoque/produtos/$productId",
        params: { productId: product!.id },
      })
    },
    onError: (err: any) => {
      handleError.call(showErrorToast, err)
    },
  })

  const isPending = createMutation.isPending || editMutation.isPending

  function onSubmit(values: ProductFormData) {
    if (isEditing) {
      editMutation.mutate(values)
    } else {
      createMutation.mutate(values)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {/* Product Type */}
        <FormField
          control={form.control}
          name="product_type_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tipo de Produto *</FormLabel>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {(productTypes ?? []).map((pt) => (
                    <SelectItem key={pt.id} value={pt.id}>
                      {pt.name} ({pt.unit_of_measure})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Name */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nome *</FormLabel>
              <FormControl>
                <Input placeholder="Nome do produto" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Unit Price */}
        <FormField
          control={form.control}
          name="unit_price"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Preço Unitário (R$) *</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={field.value}
                  onChange={(e) => field.onChange(e.target.valueAsNumber)}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Fornecedor (optional) */}
        <FormField
          control={form.control}
          name="fornecedor_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fornecedor (opcional)</FormLabel>
              <Select
                onValueChange={(val) =>
                  field.onChange(val === "none" ? undefined : val)
                }
                value={field.value ?? "none"}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o fornecedor" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="none">Nenhum</SelectItem>
                  {(fornecedores ?? []).map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.company_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Description */}
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descrição (opcional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Descrição do produto"
                  className="resize-none"
                  rows={3}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Initial Stock — only shown for new products */}
        {!isEditing && (
          <FormField
            control={form.control}
            name="initial_stock"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Estoque Inicial (opcional)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    step="0.0001"
                    min="0"
                    placeholder="0"
                    value={field.value ?? ""}
                    onChange={(e) =>
                      field.onChange(
                        e.target.value === ""
                          ? undefined
                          : e.target.valueAsNumber,
                      )
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        <div className="flex gap-2 pt-2">
          <LoadingButton type="submit" loading={isPending}>
            {isEditing ? "Salvar Alterações" : "Criar Produto"}
          </LoadingButton>
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              isEditing
                ? void navigate({
                    to: "/estoque/produtos/$productId",
                    params: { productId: product!.id },
                  })
                : void navigate({ to: "/estoque/produtos" })
            }
          >
            Cancelar
          </Button>
        </div>
      </form>
    </Form>
  )
}
