import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { OrderProcessorForm } from '@/components/orders/order-processor-form'
import { orderApi } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api')
const mockOrderApi = orderApi as jest.Mocked<typeof orderApi>

// Mock sonner
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

describe('OrderProcessorForm', () => {
  const mockOnClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders form input tab by default', () => {
    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    expect(screen.getByText(/process order/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/order reference/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/customer code/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /process order/i })).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    const submitButton = screen.getByRole('button', { name: /process order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/order reference is required/i)).toBeInTheDocument()
      expect(screen.getByText(/customer code is required/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      invoice: {
        invoice_number: 'INV-2025-001',
        total: 383,
        currency: 'EUR'
      },
      orchestration: {
        traceId: 'trace_123',
        totalProcessingTime: 2500
      }
    }
    mockOrderApi.processOrder.mockResolvedValue(mockResponse)

    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    // Fill form fields
    await user.type(screen.getByLabelText(/order reference/i), 'ORD20250617-00042')
    await user.type(screen.getByLabelText(/customer code/i), '123456')
    await user.type(screen.getByLabelText(/freightpayer code/i), '234567')
    await user.type(screen.getByLabelText(/container type iso code/i), '22G1')
    await user.type(screen.getByLabelText(/tare weight/i), '2000')
    await user.type(screen.getByLabelText(/payload/i), '21000')
    await user.type(screen.getByLabelText(/departure date/i), '2025-05-15')
    await user.type(screen.getByLabelText(/arrival date/i), '2025-05-20')

    const submitButton = screen.getByRole('button', { name: /process order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockOrderApi.processOrder).toHaveBeenCalledWith({
        Order: {
          OrderReference: 'ORD20250617-00042',
          Customer: { Code: '123456' },
          Freightpayer: { Code: '234567' },
          Container: {
            ContainerTypeIsoCode: '22G1',
            TareWeight: '2000',
            Payload: '21000',
            DangerousGoodFlag: 'N',
            TransportDirection: 'Export',
          },
          DepartureDate: '2025-05-15',
          ArrivalDate: '2025-05-20',
        },
      })
    })
  })

  it('switches to JSON input tab', async () => {
    const user = userEvent.setup()
    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    const jsonTab = screen.getByRole('tab', { name: /json input/i })
    await user.click(jsonTab)

    expect(screen.getByText(/load sample order/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/paste your order json here/i)).toBeInTheDocument()
  })

  it('loads sample order JSON', async () => {
    const user = userEvent.setup()
    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    const jsonTab = screen.getByRole('tab', { name: /json input/i })
    await user.click(jsonTab)

    const loadSampleButton = screen.getByRole('button', { name: /load sample order/i })
    await user.click(loadSampleButton)

    const textArea = screen.getByPlaceholderText(/paste your order json here/i) as HTMLTextAreaElement
    expect(textArea.value).toContain('ORD20250617-00042')
    expect(textArea.value).toContain('123456')
  })

  it('processes JSON order', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      invoice: { invoice_number: 'INV-2025-001', total: 383 }
    }
    mockOrderApi.processOrder.mockResolvedValue(mockResponse)

    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    const jsonTab = screen.getByRole('tab', { name: /json input/i })
    await user.click(jsonTab)

    const textArea = screen.getByPlaceholderText(/paste your order json here/i)
    await user.type(textArea, JSON.stringify({
      Order: {
        OrderReference: 'TEST-001',
        Customer: { Code: '123456' }
      }
    }))

    const processButton = screen.getByRole('button', { name: /process json order/i })
    await user.click(processButton)

    await waitFor(() => {
      expect(mockOrderApi.processOrder).toHaveBeenCalled()
    })
  })

  it('displays processing results', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      invoice: {
        invoice_number: 'INV-2025-001',
        total: 383,
        currency: 'EUR',
        pdf_path: '/path/to/invoice.pdf'
      },
      orchestration: {
        traceId: 'trace_123',
        totalProcessingTime: 2500,
        stageResults: {
          transformation: { success: true, processingTime: 500 },
          rating: { success: true, processingTime: 800 },
          billing: { success: true, processingTime: 1200 }
        }
      },
      warnings: ['Minor warning about pricing']
    }
    mockOrderApi.processOrder.mockResolvedValue(mockResponse)

    render(<OrderProcessorForm isOpen={true} onClose={mockOnClose} />)

    // Submit a simple form
    await user.type(screen.getByLabelText(/order reference/i), 'TEST-001')
    await user.type(screen.getByLabelText(/customer code/i), '123456')
    await user.type(screen.getByLabelText(/freightpayer code/i), '234567')
    await user.type(screen.getByLabelText(/container type iso code/i), '22G1')
    await user.type(screen.getByLabelText(/tare weight/i), '2000')
    await user.type(screen.getByLabelText(/payload/i), '21000')
    await user.type(screen.getByLabelText(/departure date/i), '2025-05-15')
    await user.type(screen.getByLabelText(/arrival date/i), '2025-05-20')

    const submitButton = screen.getByRole('button', { name: /process order/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/order processed successfully/i)).toBeInTheDocument()
      expect(screen.getByText(/INV-2025-001/)).toBeInTheDocument()
      expect(screen.getByText(/€383/)).toBeInTheDocument()
      expect(screen.getByText(/trace_123/)).toBeInTheDocument()
      expect(screen.getByText(/2500ms/)).toBeInTheDocument()
      expect(screen.getByText(/Minor warning about pricing/)).toBeInTheDocument()
    })
  })
})