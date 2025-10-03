'use client'

import { useState, useEffect } from 'react'
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
import { Upload, FileSpreadsheet, CheckCircle2, XCircle, RefreshCw, Loader2, Scale, GitBranch, Calculator } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { rulesApi } from '@/lib/api'

interface DmnFile {
  name: string
  displayName: string
  description: string
  file?: File
  uploadedAt?: string
  size?: number
}

interface RuleData {
  rule_type: string
  file_name: string
  headers: string[]
  rows: any[]
  total_count: number
}

export default function RulesPage() {
  const [activeTab, setActiveTab] = useState('dmn-files')
  const [rulesData, setRulesData] = useState<Record<string, RuleData | null>>({})
  const [loading, setLoading] = useState<Record<string, boolean>>({})
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

  const fetchRules = async (ruleType: string) => {
    if (rulesData[ruleType]) return // Already loaded

    setLoading(prev => ({ ...prev, [ruleType]: true }))
    try {
      const data = await rulesApi.getRules(ruleType)
      setRulesData(prev => ({ ...prev, [ruleType]: data }))
    } catch (error) {
      console.error(`Error fetching ${ruleType} rules:`, error)
      setRulesData(prev => ({ ...prev, [ruleType]: null }))
    } finally {
      setLoading(prev => ({ ...prev, [ruleType]: false }))
    }
  }

  // Fetch data when tab changes
  useEffect(() => {
    const ruleTypeMap: Record<string, string> = {
      'weight-class': 'weight-class',
      'service-determination': 'service-determination',
      'trip-type': 'trip-type',
      'tax-calculation': 'tax-calculation',
      'waiting-times': 'waiting-times',
      'pricing': 'pricing-main'
    }

    if (ruleTypeMap[activeTab]) {
      fetchRules(ruleTypeMap[activeTab])
    }
  }, [activeTab])

  const RulesTable = ({ ruleType, title, description }: { ruleType: string, title: string, description: string }) => {
    const data = rulesData[ruleType]
    const isLoading = loading[ruleType]

    if (isLoading) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </CardContent>
        </Card>
      )
    }

    if (!data) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent className="text-center py-12 text-gray-500">
            Failed to load rules data
          </CardContent>
        </Card>
      )
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description} - {data.file_name} ({data.total_count} rules)</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                {data.headers.map((header, idx) => (
                  <TableHead key={idx}>{header}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.rows.map((row, rowIdx) => (
                <TableRow key={rowIdx}>
                  {data.headers.map((header, cellIdx) => (
                    <TableCell key={cellIdx}>
                      {row[header] !== null && row[header] !== undefined ? String(row[header]) : '-'}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
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
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Excel Files
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {dmnFiles.length}
                </p>
                <p className="text-sm text-blue-600">
                  {dmnFiles.filter(f => f.file).length} uploaded locally
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <FileSpreadsheet className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Weight Rules
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {rulesData['weight-class']?.total_count || '-'}
                </p>
                <p className="text-sm text-gray-600">
                  classification rules
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <Scale className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Service Rules
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {rulesData['service-determination']?.total_count || '-'}
                </p>
                <p className="text-sm text-gray-600">
                  determination rules
                </p>
              </div>
              <div className="p-3 rounded-full bg-purple-100">
                <GitBranch className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Pricing Entries
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {rulesData['pricing-main']?.total_count || '-'}
                </p>
                <p className="text-sm text-gray-600">
                  main service prices
                </p>
              </div>
              <div className="p-3 rounded-full bg-yellow-100">
                <Calculator className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Rules Management Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="dmn-files">DMN Files</TabsTrigger>
          <TabsTrigger value="weight-class">Weight Classification</TabsTrigger>
          <TabsTrigger value="service-determination">Service Determination</TabsTrigger>
          <TabsTrigger value="trip-type">Trip Type</TabsTrigger>
          <TabsTrigger value="tax-calculation">Tax Calculation</TabsTrigger>
          <TabsTrigger value="waiting-times">Waiting Times</TabsTrigger>
          <TabsTrigger value="pricing">Pricing Tables</TabsTrigger>
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
                  <RefreshCw className="h-5 w-5 text-blue-600 mt-0.5" />
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

        <TabsContent value="weight-class">
          <RulesTable
            ruleType="weight-class"
            title="Weight Classification Rules"
            description="Determines weight class (20A/20B/40A/40B) based on container length and gross weight"
          />
        </TabsContent>

        <TabsContent value="service-determination">
          <RulesTable
            ruleType="service-determination"
            title="Service Determination Rules"
            description="Determines which services (NGB codes) apply based on transport conditions"
          />
        </TabsContent>

        <TabsContent value="trip-type">
          <RulesTable
            ruleType="trip-type"
            title="Trip Type Classification"
            description="Classifies trucking trips as delivery (Zustellung) or pickup (Abholung)"
          />
        </TabsContent>

        <TabsContent value="tax-calculation">
          <RulesTable
            ruleType="tax-calculation"
            title="Tax Calculation Rules"
            description="VAT rules based on transport direction and customs procedures"
          />
        </TabsContent>

        <TabsContent value="waiting-times">
          <RulesTable
            ruleType="waiting-times"
            title="Waiting Times Rules"
            description="Free waiting time units per customer"
          />
        </TabsContent>

        <TabsContent value="pricing">
          <RulesTable
            ruleType="pricing-main"
            title="Main Service Pricing"
            description="Service pricing by customer, weight class, and route"
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}