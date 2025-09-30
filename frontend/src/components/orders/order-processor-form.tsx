'use client'

import { useState, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { orderApi } from '@/lib/api'
import { toast } from 'sonner'
import { FileText, Upload } from 'lucide-react'

interface ProcessingResult {
  invoice?: {
    invoice_number: string
    total: string | number
    currency: string
    pdf_path?: string
  }
  orchestration?: {
    traceId: string
    totalProcessingTime: number
    stageResults?: Record<string, {
      success: boolean
      processingTime: number
    }>
  }
  warnings?: string[]
}

interface ApiError {
  response?: {
    data?: {
      error?: {
        message: string
      }
    }
  }
}

const orderSchema = z.object({
  orderReference: z.string().min(1, 'Order reference is required'),
  customerCode: z.string().min(1, 'Customer code is required'),
  freightpayerCode: z.string().min(1, 'Freightpayer code is required'),
  containerTypeIsoCode: z.string().min(1, 'Container type is required'),
  tareWeight: z.string().min(1, 'Tare weight is required'),
  payload: z.string().min(1, 'Payload is required'),
  dangerousGoodFlag: z.enum(['J', 'N']),
  transportDirection: z.enum(['Export', 'Import', 'Domestic']),
  departureDate: z.string().min(1, 'Departure date is required'),
  arrivalDate: z.string().min(1, 'Arrival date is required'),
})

type OrderForm = z.infer<typeof orderSchema>

interface OrderProcessorFormProps {
  isOpen: boolean
  onClose: () => void
}

export function OrderProcessorForm({ isOpen, onClose }: OrderProcessorFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [jsonInput, setJsonInput] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const form = useForm<OrderForm>({
    resolver: zodResolver(orderSchema),
    defaultValues: {
      orderReference: '',
      customerCode: '',
      freightpayerCode: '',
      containerTypeIsoCode: '',
      tareWeight: '',
      payload: '',
      dangerousGoodFlag: 'N',
      transportDirection: 'Export',
      departureDate: '',
      arrivalDate: '',
    },
  })

  const onSubmit = async (data: OrderForm) => {
    console.log('[OrderProcessor] Starting form submission')
    console.log('[OrderProcessor] Form data:', data)
    setIsLoading(true)

    try {
      // Transform form data to API format
      const orderData = {
        Order: {
          OrderReference: data.orderReference,
          Customer: { Code: data.customerCode },
          Freightpayer: { Code: data.freightpayerCode },
          Container: {
            ContainerTypeIsoCode: data.containerTypeIsoCode,
            TareWeight: data.tareWeight,
            Payload: data.payload,
            DangerousGoodFlag: data.dangerousGoodFlag,
            TransportDirection: data.transportDirection,
          },
          DepartureDate: data.departureDate,
          ArrivalDate: data.arrivalDate,
        },
      }

      console.log('[OrderProcessor] Transformed order data:', orderData)
      console.log('[OrderProcessor] Calling API to process order...')
      const response = await orderApi.processOrder(orderData)
      console.log('[OrderProcessor] API response:', response)

      setResult(response)
      toast.success('Order processed successfully!')
    } catch (error) {
      console.error('[OrderProcessor] Error processing order:', error)
      const apiError = error as ApiError
      console.error('[OrderProcessor] API error details:', apiError.response?.data)
      toast.error(apiError.response?.data?.error?.message || 'Order processing failed')
    } finally {
      setIsLoading(false)
      console.log('[OrderProcessor] Form submission complete')
    }
  }

  const processJsonOrder = async () => {
    console.log('[OrderProcessor] Starting JSON order processing')

    if (!jsonInput.trim()) {
      console.warn('[OrderProcessor] No JSON input provided')
      toast.error('Please enter JSON order data')
      return
    }

    console.log('[OrderProcessor] Raw JSON input:', jsonInput)
    setIsLoading(true)

    try {
      const orderData = JSON.parse(jsonInput)
      console.log('[OrderProcessor] Parsed order data:', orderData)

      console.log('[OrderProcessor] Calling API to process order...')
      const response = await orderApi.processOrder(orderData)
      console.log('[OrderProcessor] API response:', response)

      setResult(response)
      toast.success('Order processed successfully!')
    } catch (error) {
      console.error('[OrderProcessor] Error processing order:', error)

      if (error instanceof SyntaxError) {
        console.error('[OrderProcessor] JSON syntax error:', error.message)
        toast.error('Invalid JSON format')
      } else {
        const apiError = error as ApiError
        console.error('[OrderProcessor] API error:', apiError.response?.data)
        toast.error(apiError.response?.data?.error?.message || 'Order processing failed')
      }
    } finally {
      setIsLoading(false)
      console.log('[OrderProcessor] Processing complete')
    }
  }

  const loadSampleOrder = () => {
    const sampleOrder = {
      Order: {
        OrderReference: "ORD20250617-00042",
        Customer: { Code: "123456" },
        Freightpayer: { Code: "234567" },
        Container: {
          ContainerTypeIsoCode: "22G1",
          TareWeight: "2000",
          Payload: "21000",
          DangerousGoodFlag: "J",
          TransportDirection: "Export"
        },
        DepartureDate: "2025-05-15",
        ArrivalDate: "2025-05-20",
        TruckingServices: [
          {
            TruckingCode: "LB",
            Station: "80155283"
          }
        ],
        AdditionalServices: [
          {
            ServiceCode: "N1",
            Quantity: 5
          }
        ]
      }
    }
    setJsonInput(JSON.stringify(sampleOrder, null, 2))
  }

  const handleClose = () => {
    setResult(null)
    form.reset()
    setJsonInput('')
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Process Order</DialogTitle>
          <DialogDescription>
            Submit an operational order for processing through the billing pipeline
          </DialogDescription>
        </DialogHeader>

        {result ? (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-green-600">Order Processed Successfully!</CardTitle>
                <CardDescription>
                  Invoice generated with total: {result.invoice?.total ? `€${result.invoice.total}` : 'N/A'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {result.invoice && (
                    <div>
                      <h4 className="font-medium mb-2">Invoice Details:</h4>
                      <div className="bg-gray-50 p-3 rounded text-sm">
                        <p><strong>Invoice Number:</strong> {result.invoice.invoice_number}</p>
                        <p><strong>Total Amount:</strong> €{result.invoice.total}</p>
                        <p><strong>Currency:</strong> {result.invoice.currency}</p>
                        {result.invoice.pdf_path && (
                          <p><strong>PDF Generated:</strong> {result.invoice.pdf_path}</p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.orchestration && (
                    <div>
                      <h4 className="font-medium mb-2">Processing Details:</h4>
                      <div className="bg-gray-50 p-3 rounded text-sm">
                        <p><strong>Trace ID:</strong> {result.orchestration.traceId}</p>
                        <p><strong>Total Processing Time:</strong> {result.orchestration.totalProcessingTime}ms</p>
                        {result.orchestration.stageResults && (
                          <div className="mt-2">
                            <p><strong>Stage Results:</strong></p>
                            <ul className="ml-4 mt-1">
                              {Object.entries(result.orchestration.stageResults).map(([stage, details]) => (
                                <li key={stage}>
                                  {stage}: {details.success ? '✅' : '❌'} ({details.processingTime}ms)
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {result.warnings && result.warnings.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2 text-yellow-600">Warnings:</h4>
                      <div className="bg-yellow-50 p-3 rounded text-sm">
                        {result.warnings.map((warning: string, index: number) => (
                          <p key={index}>{warning}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <DialogFooter>
              <Button onClick={handleClose}>Close</Button>
              <Button onClick={() => setResult(null)} variant="outline">
                Process Another Order
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <Tabs defaultValue="form" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="form">Form Input</TabsTrigger>
              <TabsTrigger value="json">JSON Input</TabsTrigger>
              <TabsTrigger value="file">File Upload</TabsTrigger>
            </TabsList>

            <TabsContent value="form">
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="orderReference">Order Reference</Label>
                    <Input
                      id="orderReference"
                      placeholder="ORD20250617-00042"
                      {...form.register('orderReference')}
                    />
                    {form.formState.errors.orderReference && (
                      <p className="text-sm text-red-600">
                        {form.formState.errors.orderReference.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customerCode">Customer Code</Label>
                    <Input
                      id="customerCode"
                      placeholder="123456"
                      {...form.register('customerCode')}
                    />
                    {form.formState.errors.customerCode && (
                      <p className="text-sm text-red-600">
                        {form.formState.errors.customerCode.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="freightpayerCode">Freightpayer Code</Label>
                    <Input
                      id="freightpayerCode"
                      placeholder="234567"
                      {...form.register('freightpayerCode')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="containerTypeIsoCode">Container Type ISO Code</Label>
                    <Input
                      id="containerTypeIsoCode"
                      placeholder="22G1"
                      {...form.register('containerTypeIsoCode')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tareWeight">Tare Weight (kg)</Label>
                    <Input
                      id="tareWeight"
                      placeholder="2000"
                      {...form.register('tareWeight')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="payload">Payload (kg)</Label>
                    <Input
                      id="payload"
                      placeholder="21000"
                      {...form.register('payload')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dangerousGoodFlag">Dangerous Goods</Label>
                    <select
                      id="dangerousGoodFlag"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...form.register('dangerousGoodFlag')}
                    >
                      <option value="N">No</option>
                      <option value="J">Yes</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="transportDirection">Transport Direction</Label>
                    <select
                      id="transportDirection"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...form.register('transportDirection')}
                    >
                      <option value="Export">Export</option>
                      <option value="Import">Import</option>
                      <option value="Domestic">Domestic</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="departureDate">Departure Date</Label>
                    <Input
                      id="departureDate"
                      type="date"
                      {...form.register('departureDate')}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="arrivalDate">Arrival Date</Label>
                    <Input
                      id="arrivalDate"
                      type="date"
                      {...form.register('arrivalDate')}
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Processing...' : 'Process Order'}
                  </Button>
                </DialogFooter>
              </form>
            </TabsContent>

            <TabsContent value="json" className="space-y-4">
              <div className="space-y-4">
                <div className="flex space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={loadSampleOrder}
                    className="flex items-center space-x-1"
                  >
                    <FileText className="h-4 w-4" />
                    <span>Load Sample Order</span>
                  </Button>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="jsonInput">Order JSON</Label>
                  <textarea
                    id="jsonInput"
                    className="w-full h-96 p-3 border rounded-md font-mono text-sm"
                    placeholder="Paste your order JSON here..."
                    value={jsonInput}
                    onChange={(e) => setJsonInput(e.target.value)}
                  />
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button onClick={processJsonOrder} disabled={isLoading}>
                    {isLoading ? 'Processing...' : 'Process JSON Order'}
                  </Button>
                </DialogFooter>
              </div>
            </TabsContent>

            <TabsContent value="file" className="space-y-4">
              <div className="space-y-4">
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                    isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDrop={(e) => {
                    e.preventDefault()
                    setIsDragging(false)
                    const file = e.dataTransfer.files?.[0]
                    if (file && file.type === 'application/json') {
                      const reader = new FileReader()
                      reader.onload = (event) => {
                        setJsonInput(event.target?.result as string)
                      }
                      reader.readAsText(file)
                    } else {
                      toast.error('Please upload a valid JSON file')
                    }
                  }}
                  onDragOver={(e) => {
                    e.preventDefault()
                    setIsDragging(true)
                  }}
                  onDragLeave={() => {
                    setIsDragging(false)
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    Drag and drop a JSON file, or click to select
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) {
                        const reader = new FileReader()
                        reader.onload = (event) => {
                          setJsonInput(event.target?.result as string)
                        }
                        reader.readAsText(file)
                      }
                    }}
                  />
                  <Button
                    variant="outline"
                    className="mt-2"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      fileInputRef.current?.click()
                    }}
                  >
                    Select File
                  </Button>
                </div>

                {jsonInput && (
                  <div className="space-y-2">
                    <Label>Loaded File Content</Label>
                    <pre className="w-full h-32 p-3 border rounded-md font-mono text-sm bg-gray-50 overflow-auto">
                      {jsonInput}
                    </pre>
                  </div>
                )}

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={handleClose}>
                    Cancel
                  </Button>
                  <Button onClick={processJsonOrder} disabled={isLoading || !jsonInput}>
                    {isLoading ? 'Processing...' : 'Process File Order'}
                  </Button>
                </DialogFooter>
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  )
}