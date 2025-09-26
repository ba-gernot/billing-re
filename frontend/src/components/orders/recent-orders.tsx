'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { orderApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Eye, Download, RefreshCw } from 'lucide-react'

interface Order {
  id: string
  orderReference: string
  customerCode: string
  status: string
  totalAmount: number
  currency: string
  createdAt: string
  invoiceNumber?: string
}

export function RecentOrders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    setIsLoading(true)
    try {
      const response = await orderApi.getOrderHistory({ limit: 20 })
      setOrders(response.orders || [])
    } catch (error) {
      console.error('Failed to load orders:', error)
      // Use mock data for demo
      setOrders([
        {
          id: '1',
          orderReference: 'ORD20250617-00042',
          customerCode: '123456',
          status: 'completed',
          totalAmount: 383,
          currency: 'EUR',
          createdAt: '2025-05-17T10:30:00Z',
          invoiceNumber: 'INV-2025-001'
        },
        {
          id: '2',
          orderReference: 'ORD20250617-00043',
          customerCode: '234567',
          status: 'processing',
          totalAmount: 245,
          currency: 'EUR',
          createdAt: '2025-05-17T11:15:00Z'
        },
        {
          id: '3',
          orderReference: 'ORD20250617-00044',
          customerCode: '123456',
          status: 'completed',
          totalAmount: 567,
          currency: 'EUR',
          createdAt: '2025-05-17T12:00:00Z',
          invoiceNumber: 'INV-2025-002'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Completed</Badge>
      case 'processing':
        return <Badge className="bg-yellow-100 text-yellow-800">Processing</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Recent Orders</CardTitle>
          <CardDescription>
            Latest order processing results
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadOrders}
          disabled={isLoading}
          className="flex items-center space-x-1"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        ) : orders.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order Reference</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Invoice</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-medium">
                    {order.orderReference}
                  </TableCell>
                  <TableCell>{order.customerCode}</TableCell>
                  <TableCell>{getStatusBadge(order.status)}</TableCell>
                  <TableCell>
                    {formatCurrency(order.totalAmount, order.currency)}
                  </TableCell>
                  <TableCell>
                    {order.invoiceNumber || '-'}
                  </TableCell>
                  <TableCell>
                    {formatDate(order.createdAt)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      {order.invoiceNumber && (
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No orders found. Process your first order to see results here.
          </div>
        )}
      </CardContent>
    </Card>
  )
}