'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus, FileText, DollarSign, AlertTriangle, CheckCircle } from 'lucide-react'
import { OrderProcessorForm } from '@/components/orders/order-processor-form'
import { RecentOrders } from '@/components/orders/recent-orders'
import { InvoicesSummary } from '@/components/invoices/invoices-summary'
import { useServiceHealth } from '@/hooks/use-service-health'
import { ServiceStatus } from '@/components/dashboard/service-status'

// Color class mappings for Tailwind JIT compilation
const colorClasses = {
  blue: {
    bg: 'bg-blue-100',
    text: 'text-blue-600',
  },
  green: {
    bg: 'bg-green-100',
    text: 'text-green-600',
  },
  yellow: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-600',
  },
  red: {
    bg: 'bg-red-100',
    text: 'text-red-600',
  },
} as const

type ColorKey = keyof typeof colorClasses

export default function DashboardPage() {
  const [showOrderForm, setShowOrderForm] = useState(false)
  const { health, isLoading } = useServiceHealth(30000) // Auto-refresh every 30 seconds

  const dashboardStats = [
    {
      title: 'Orders Today',
      value: '23',
      change: '+12%',
      icon: FileText,
      color: 'blue' as ColorKey
    },
    {
      title: 'Total Revenue',
      value: '€12,847',
      change: '+8.2%',
      icon: DollarSign,
      color: 'green' as ColorKey
    },
    {
      title: 'Pending Invoices',
      value: '7',
      change: '-3',
      icon: AlertTriangle,
      color: 'yellow' as ColorKey
    },
    {
      title: 'Completed Today',
      value: '18',
      change: '+5',
      icon: CheckCircle,
      color: 'green' as ColorKey
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Billing RE System - Transport Logistics Billing
          </p>
        </div>
        <Button
          onClick={() => setShowOrderForm(true)}
          className="flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Process Order</span>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      {stat.title}
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stat.value}
                    </p>
                    <p className={`text-sm ${
                      stat.change.startsWith('+') ? 'text-green-600' :
                      stat.change.startsWith('-') ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {stat.change} from yesterday
                    </p>
                  </div>
                  <div className={`p-3 rounded-full ${colorClasses[stat.color].bg}`}>
                    <Icon className={`h-6 w-6 ${colorClasses[stat.color].text}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="orders">Recent Orders</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common billing operations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setShowOrderForm(true)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Process New Order
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="mr-2 h-4 w-4" />
                  View All Orders
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <DollarSign className="mr-2 h-4 w-4" />
                  Generate Invoice Report
                </Button>
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
                <CardDescription>
                  Service health and performance (auto-refresh: 30s)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoading && !health ? (
                  // Initial loading state
                  <>
                    <ServiceStatus name="api-gateway" status="loading" displayName="API Gateway" />
                    <ServiceStatus name="transformation" status="loading" displayName="Transformation Service" />
                    <ServiceStatus name="rating" status="loading" displayName="Rating Service" />
                    <ServiceStatus name="billing" status="loading" displayName="Billing Service" />
                  </>
                ) : health ? (
                  // Dynamic service status from API
                  health.services.map((service) => (
                    <ServiceStatus
                      key={service.service}
                      name={service.service}
                      status={service.status}
                      displayName={
                        service.service === 'api-gateway'
                          ? 'API Gateway'
                          : `${service.service.charAt(0).toUpperCase() + service.service.slice(1)} Service`
                      }
                    />
                  ))
                ) : (
                  // Fallback if health data unavailable
                  <div className="text-sm text-gray-500">
                    Unable to fetch service health status
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="orders">
          <RecentOrders />
        </TabsContent>

        <TabsContent value="invoices">
          <InvoicesSummary />
        </TabsContent>
      </Tabs>

      {/* Order Processing Form Modal */}
      {showOrderForm && (
        <OrderProcessorForm
          isOpen={showOrderForm}
          onClose={() => setShowOrderForm(false)}
        />
      )}
    </div>
  )
}