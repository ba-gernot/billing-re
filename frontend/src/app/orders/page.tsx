'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RecentOrders } from '@/components/orders/recent-orders'
import { OrderProcessorForm } from '@/components/orders/order-processor-form'
import { Plus, FileText, Clock, CheckCircle, AlertTriangle } from 'lucide-react'

export default function OrdersPage() {
  const [showOrderForm, setShowOrderForm] = useState(false)

  const orderStats = [
    {
      title: 'Total Orders',
      value: '156',
      change: '+12 today',
      icon: FileText,
      color: 'blue'
    },
    {
      title: 'Processing',
      value: '8',
      change: 'In progress',
      icon: Clock,
      color: 'yellow'
    },
    {
      title: 'Completed',
      value: '142',
      change: '+10 today',
      icon: CheckCircle,
      color: 'green'
    },
    {
      title: 'Failed',
      value: '6',
      change: 'Need attention',
      icon: AlertTriangle,
      color: 'red'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-600">
            Process and manage transport logistics orders
          </p>
        </div>
        <Button
          onClick={() => setShowOrderForm(true)}
          className="flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Process New Order</span>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {orderStats.map((stat, index) => {
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
                      stat.color === 'green' ? 'text-green-600' :
                      stat.color === 'yellow' ? 'text-yellow-600' :
                      stat.color === 'red' ? 'text-red-600' :
                      'text-blue-600'
                    }`}>
                      {stat.change}
                    </p>
                  </div>
                  <div className={`p-3 rounded-full bg-${stat.color}-100`}>
                    <Icon className={`h-6 w-6 text-${stat.color}-600`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Processing Pipeline Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Order Processing Pipeline</CardTitle>
          <CardDescription>
            Overview of the 6-stage billing pipeline
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            {[
              { stage: '1', name: 'Input', desc: 'Operational Order', status: 'active' },
              { stage: '2', name: 'Transform', desc: 'Service Decomposition', status: 'active' },
              { stage: '3', name: 'Rate', desc: 'Service Determination', status: 'active' },
              { stage: '4', name: 'Price', desc: 'Price Calculation', status: 'active' },
              { stage: '5', name: 'Bill', desc: 'Document Aggregation', status: 'active' },
              { stage: '6', name: 'Invoice', desc: 'PDF Generation', status: 'active' }
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-white font-bold ${
                  step.status === 'active' ? 'bg-green-500' : 'bg-gray-300'
                }`}>
                  {step.stage}
                </div>
                <h4 className="mt-2 font-medium text-gray-900">{step.name}</h4>
                <p className="text-sm text-gray-500">{step.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900">Target Calculation Example</h4>
            <p className="text-sm text-blue-700 mt-1">
              Order ORD20250617-00042 → Main Service (€100) + Trucking (€18) + Security (€15) + Waiting (€250) = <strong>€383 total</strong>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Recent Orders */}
      <RecentOrders />

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