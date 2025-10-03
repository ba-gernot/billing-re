'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Plus, Edit, Eye, Database, DollarSign, Cog, Upload, FileSpreadsheet, CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'

interface ServiceRule {
  id: string
  name: string
  conditions: string
  serviceCode: string
  description: string
  validFrom: string
  validTo: string
  isActive: boolean
}

interface PricingRule {
  id: string
  customerCode: string
  serviceCode: string
  weightClass: string
  basePrice: number
  minimumPrice?: number
  validFrom: string
  validTo: string
  isActive: boolean
}

interface DmnFile {
  name: string
  displayName: string
  description: string
  file?: File
  uploadedAt?: string
  size?: number
}

export default function RulesPage() {
  const [activeTab, setActiveTab] = useState('dmn-files')
  const [dmnFiles, setDmnFiles] = useState<DmnFile[]>([
    {
      name: '5_Regeln_Gewichtsklassen.xlsx',
      displayName: 'Weight Classification',
      description: 'Rules for determining weight classes (20A/20B/40A/40B) based on container dimensions and weight'
    },
    {
      name: '4_Regeln_Leistungsermittlung.xlsx',
      displayName: 'Service Determination',
      description: 'Rules for determining which services apply based on transport type, conditions, and date ranges'
    },
    {
      name: '3_Regeln_Fahrttyp.xlsx',
      displayName: 'Trip Type',
      description: 'Rules for classifying trips as delivery (Zustellung) or pickup (Abholung)'
    },
    {
      name: '3_1_Regeln_Steuerberechnung.xlsx',
      displayName: 'Tax Calculation',
      description: 'VAT and tax rules based on transport direction (Export/Import/Domestic)'
    },
    {
      name: '3_Regeln_Wartezeiten.xlsx',
      displayName: 'Waiting Times',
      description: 'Rules for calculating waiting time charges'
    },
    {
      name: '6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx',
      displayName: 'Main Service Prices',
      description: 'Price table for main transport services with individual pricing'
    },
    {
      name: '6_Preistabelle_Nebenleistungen.xlsx',
      displayName: 'Additional Service Prices',
      description: 'Price table for additional services and surcharges'
    }
  ])

  const handleFileUpload = (fileName: string, file: File) => {
    setDmnFiles(prevFiles =>
      prevFiles.map(f =>
        f.name === fileName
          ? { ...f, file, uploadedAt: new Date().toISOString(), size: file.size }
          : f
      )
    )
  }

  const handleFileRemove = (fileName: string) => {
    setDmnFiles(prevFiles =>
      prevFiles.map(f =>
        f.name === fileName
          ? { name: f.name, displayName: f.displayName, description: f.description }
          : f
      )
    )
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Mock data for service rules
  const serviceRules: ServiceRule[] = [
    {
      id: '1',
      name: 'KV Dangerous Goods Security',
      conditions: 'KV + Dangerous + Date Range',
      serviceCode: '456',
      description: 'Security surcharge for KV dangerous goods',
      validFrom: '2025-05-01',
      validTo: '2025-08-31',
      isActive: true
    },
    {
      id: '2',
      name: 'Generic Main Service',
      conditions: 'Main Service + Any',
      serviceCode: '111',
      description: 'Standard main transport service',
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    },
    {
      id: '3',
      name: 'Trucking Service',
      conditions: 'Trucking + Any',
      serviceCode: '222',
      description: 'Standard trucking service',
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    },
    {
      id: '4',
      name: 'Station Security',
      conditions: 'Station 80155283 OR 80137943',
      serviceCode: '333',
      description: 'Security service for specific stations',
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    }
  ]

  // Mock data for pricing rules
  const pricingRules: PricingRule[] = [
    {
      id: '1',
      customerCode: '123456',
      serviceCode: '111',
      weightClass: '20B',
      basePrice: 100,
      minimumPrice: 100,
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    },
    {
      id: '2',
      customerCode: '123456',
      serviceCode: '222',
      weightClass: 'ANY',
      basePrice: 18,
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    },
    {
      id: '3',
      customerCode: '123456',
      serviceCode: '456',
      weightClass: 'ANY',
      basePrice: 15,
      validFrom: '2025-05-01',
      validTo: '2025-08-31',
      isActive: true
    },
    {
      id: '4',
      customerCode: '123456',
      serviceCode: '789',
      weightClass: 'ANY',
      basePrice: 50,
      validFrom: '2025-01-01',
      validTo: '2025-12-31',
      isActive: true
    }
  ]

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge className="bg-green-100 text-green-800">Active</Badge>
    ) : (
      <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Rules Management</h1>
          <p className="text-gray-600">
            Manage business rules and pricing configurations
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" className="flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Import Rules</span>
          </Button>
          <Button className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>New Rule</span>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Service Rules
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {serviceRules.filter(rule => rule.isActive).length}
                </p>
                <p className="text-sm text-green-600">
                  {serviceRules.filter(rule => rule.isActive).length} active
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <Cog className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Pricing Rules
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {pricingRules.filter(rule => rule.isActive).length}
                </p>
                <p className="text-sm text-green-600">
                  {pricingRules.filter(rule => rule.isActive).length} active
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Customers
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Set(pricingRules.map(rule => rule.customerCode)).size}
                </p>
                <p className="text-sm text-gray-600">
                  with custom pricing
                </p>
              </div>
              <div className="p-3 rounded-full bg-purple-100">
                <Database className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Avg. Base Price
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  €{Math.round(pricingRules.reduce((sum, rule) => sum + rule.basePrice, 0) / pricingRules.length)}
                </p>
                <p className="text-sm text-gray-600">
                  across all services
                </p>
              </div>
              <div className="p-3 rounded-full bg-yellow-100">
                <DollarSign className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rules Management Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="dmn-files">DMN Files</TabsTrigger>
          <TabsTrigger value="service-rules">Service Rules</TabsTrigger>
          <TabsTrigger value="pricing-rules">Pricing Rules</TabsTrigger>
          <TabsTrigger value="weight-classes">Weight Classes</TabsTrigger>
          <TabsTrigger value="tax-rules">Tax Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="dmn-files">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>DMN Rule Files</CardTitle>
                <CardDescription>
                  Upload and manage XLSX files containing DMN business rules. Changes are automatically detected on the next API call.
                </CardDescription>
              </CardHeader>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {dmnFiles.map((dmnFile) => (
                <Card key={dmnFile.name} className="border-2 hover:border-gray-300 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${dmnFile.file ? 'bg-green-100' : 'bg-gray-100'}`}>
                          <FileSpreadsheet className={`h-5 w-5 ${dmnFile.file ? 'text-green-600' : 'text-gray-400'}`} />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{dmnFile.displayName}</CardTitle>
                          <p className="text-sm text-gray-500 font-mono mt-1">{dmnFile.name}</p>
                        </div>
                      </div>
                      {dmnFile.file ? (
                        <Badge className="bg-green-100 text-green-800 flex items-center space-x-1">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Uploaded</span>
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="flex items-center space-x-1">
                          <XCircle className="h-3 w-3" />
                          <span>No file</span>
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-gray-600">{dmnFile.description}</p>

                    {dmnFile.file && (
                      <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">File size:</span>
                          <span className="font-medium">{formatFileSize(dmnFile.size!)}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Uploaded:</span>
                          <span className="font-medium">{formatDate(dmnFile.uploadedAt!)}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">File name:</span>
                          <span className="font-medium truncate ml-2">{dmnFile.file.name}</span>
                        </div>
                      </div>
                    )}

                    {!dmnFile.file && (
                      <label className="block border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400 transition-colors">
                        <input
                          type="file"
                          accept=".xlsx"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0]
                            if (file) {
                              handleFileUpload(dmnFile.name, file)
                            }
                            e.target.value = ''
                          }}
                        />
                        <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-600 mb-1">
                          Drop .xlsx file here or click to browse
                        </p>
                        <p className="text-xs text-gray-500">
                          Upload {dmnFile.name}
                        </p>
                      </label>
                    )}

                    {dmnFile.file && (
                      <div className="flex space-x-2">
                        <label className="flex-1">
                          <input
                            type="file"
                            accept=".xlsx"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) {
                                handleFileUpload(dmnFile.name, file)
                              }
                              e.target.value = ''
                            }}
                          />
                          <Button
                            variant="outline"
                            className="w-full flex items-center space-x-2"
                            asChild
                          >
                            <span className="cursor-pointer">
                              <RefreshCw className="h-4 w-4" />
                              <span>Replace File</span>
                            </span>
                          </Button>
                        </label>

                        <Button
                          variant="ghost"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleFileRemove(dmnFile.name)}
                        >
                          Remove
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <Database className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-blue-900">Auto-reload enabled</p>
                    <p className="text-blue-700 mt-1">
                      Changes to XLSX files are automatically detected on the next API call. No service restart required.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="service-rules">
          <Card>
            <CardHeader>
              <CardTitle>Service Determination Rules</CardTitle>
              <CardDescription>
                Rules that determine which services apply to an order based on conditions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rule Name</TableHead>
                    <TableHead>Conditions</TableHead>
                    <TableHead>Service Code</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Valid Period</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {serviceRules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell className="font-medium">
                        {rule.name}
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {rule.conditions}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{rule.serviceCode}</Badge>
                      </TableCell>
                      <TableCell>{rule.description}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{formatDate(rule.validFrom)}</div>
                          <div className="text-gray-500">to {formatDate(rule.validTo)}</div>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(rule.isActive)}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pricing-rules">
          <Card>
            <CardHeader>
              <CardTitle>Pricing Rules</CardTitle>
              <CardDescription>
                Customer-specific and fallback pricing for services
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer Code</TableHead>
                    <TableHead>Service Code</TableHead>
                    <TableHead>Weight Class</TableHead>
                    <TableHead>Base Price</TableHead>
                    <TableHead>Minimum Price</TableHead>
                    <TableHead>Valid Period</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pricingRules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell className="font-medium">
                        {rule.customerCode}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{rule.serviceCode}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge>{rule.weightClass}</Badge>
                      </TableCell>
                      <TableCell>
                        {formatCurrency(rule.basePrice)}
                      </TableCell>
                      <TableCell>
                        {rule.minimumPrice ? formatCurrency(rule.minimumPrice) : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{formatDate(rule.validFrom)}</div>
                          <div className="text-gray-500">to {formatDate(rule.validTo)}</div>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(rule.isActive)}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="weight-classes">
          <Card>
            <CardHeader>
              <CardTitle>Weight Classification Rules</CardTitle>
              <CardDescription>
                Rules for determining weight classes based on container dimensions and weight
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-medium mb-2">20ft Containers</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>≤20 tons:</span>
                          <Badge>20A</Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>{'>'} 20 tons:</span>
                          <Badge>20B</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-medium mb-2">40ft Containers</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>≤25 tons:</span>
                          <Badge>40A</Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>{'>'} 25 tons:</span>
                          <Badge>40B</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                <div className="text-sm text-gray-600">
                  <p><strong>Note:</strong> Weight classes are automatically calculated based on container length and gross weight (tare + payload).</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tax-rules">
          <Card>
            <CardHeader>
              <CardTitle>Tax Calculation Rules</CardTitle>
              <CardDescription>
                VAT and tax rules based on transport direction and countries
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Transport Direction</TableHead>
                      <TableHead>Countries</TableHead>
                      <TableHead>VAT Rate</TableHead>
                      <TableHead>Tax Case</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell><Badge>Export</Badge></TableCell>
                      <TableCell>DE → Non-EU</TableCell>
                      <TableCell>0%</TableCell>
                      <TableCell>§4 No. 3a UStG</TableCell>
                      <TableCell>Export delivery exemption</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><Badge>Import</Badge></TableCell>
                      <TableCell>Non-EU → DE</TableCell>
                      <TableCell>Reverse</TableCell>
                      <TableCell>Reverse Charge</TableCell>
                      <TableCell>Customer handles VAT</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><Badge>Domestic</Badge></TableCell>
                      <TableCell>DE → DE</TableCell>
                      <TableCell>19%</TableCell>
                      <TableCell>Standard</TableCell>
                      <TableCell>Standard German VAT</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}