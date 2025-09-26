import axios from 'axios'
import { authApi, orderApi, invoiceApi } from '@/lib/api'

// Mock axios
jest.mock('axios')
const mockAxios = axios as jest.Mocked<typeof axios>

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    })
  })

  describe('authApi', () => {
    it('should login with credentials', async () => {
      const mockResponse = {
        data: {
          token: 'mock-token',
          user: { email: 'test@example.com', role: 'ADMIN' }
        }
      }
      const mockPost = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        post: mockPost,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await authApi.login({
        email: 'test@example.com',
        password: 'password123'
      })

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('should verify token', async () => {
      const mockResponse = {
        data: {
          valid: true,
          user: { email: 'test@example.com' }
        }
      }
      const mockGet = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        get: mockGet,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await authApi.verify()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/auth/verify')
      expect(result).toEqual(mockResponse.data)
    })

    it('should logout user', async () => {
      const mockResponse = { data: { message: 'Logged out' } }
      const mockPost = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        post: mockPost,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const localStorageRemoveItem = jest.fn()
      Object.defineProperty(window, 'localStorage', {
        value: { removeItem: localStorageRemoveItem },
        writable: true,
      })

      const result = await authApi.logout()

      expect(mockPost).toHaveBeenCalledWith('/api/v1/auth/logout')
      expect(localStorageRemoveItem).toHaveBeenCalledWith('auth_token')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('orderApi', () => {
    it('should process order', async () => {
      const orderData = {
        Order: {
          OrderReference: 'ORD-001',
          Customer: { Code: '123456' }
        }
      }
      const mockResponse = {
        data: {
          invoice: { invoice_number: 'INV-001', total: 383 }
        }
      }
      const mockPost = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        post: mockPost,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await orderApi.processOrder(orderData)

      expect(mockPost).toHaveBeenCalledWith('/api/v1/process-order', orderData)
      expect(result).toEqual(mockResponse.data)
    })

    it('should get order history with params', async () => {
      const params = { page: 1, limit: 10, customer_id: '123456' }
      const mockResponse = {
        data: {
          orders: [
            { id: '1', orderReference: 'ORD-001' }
          ]
        }
      }
      const mockGet = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        get: mockGet,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await orderApi.getOrderHistory(params)

      expect(mockGet).toHaveBeenCalledWith('/api/v1/orders', { params })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('invoiceApi', () => {
    it('should get invoices', async () => {
      const mockResponse = {
        data: {
          invoices: [
            { id: '1', invoiceNumber: 'INV-001' }
          ]
        }
      }
      const mockGet = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        get: mockGet,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await invoiceApi.getInvoices()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/invoices', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })

    it('should download invoice PDF', async () => {
      const mockBlob = new Blob(['PDF content'])
      const mockResponse = { data: mockBlob }
      const mockGet = jest.fn().mockResolvedValue(mockResponse)
      mockAxios.create.mockReturnValue({
        get: mockGet,
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      } as any)

      const result = await invoiceApi.downloadInvoicePdf('INV-001')

      expect(mockGet).toHaveBeenCalledWith('/api/v1/invoices/INV-001/pdf', {
        responseType: 'blob'
      })
      expect(result).toEqual(mockBlob)
    })
  })
})