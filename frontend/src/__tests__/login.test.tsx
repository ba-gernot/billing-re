import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '@/app/login/page'
import { authApi } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api')
const mockAuthApi = authApi as jest.Mocked<typeof authApi>

// Mock the auth store
const mockLogin = jest.fn()
jest.mock('@/lib/auth', () => ({
  useAuth: () => ({
    login: mockLogin,
    isAuthenticated: false,
  }),
}))

describe('Login Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthApi.getDemoUsers.mockResolvedValue({
      demoUsers: [
        {
          email: 'admin@billing-re.com',
          role: 'SYSTEM_ADMIN',
          name: 'System Administrator',
          loginHint: 'Password is: admin123'
        }
      ]
    })
  })

  it('renders login form', async () => {
    render(<LoginPage />)

    expect(screen.getByRole('heading', { name: /billing re system/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('displays demo users', async () => {
    render(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByText(/demo users/i)).toBeInTheDocument()
      expect(screen.getByText(/system administrator/i)).toBeInTheDocument()
    })
  })

  it('validates form inputs', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const signInButton = screen.getByRole('button', { name: /sign in/i })

    // Try to submit without filling fields
    await user.click(signInButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
      expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
    })
  })

  it('submits login form with valid data', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const signInButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'admin@billing-re.com')
    await user.type(passwordInput, 'admin123')
    await user.click(signInButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'admin@billing-re.com',
        password: 'admin123',
        role: '',
      })
    })
  })

  it('auto-fills demo user credentials', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    await waitFor(() => {
      expect(screen.getByText(/system administrator/i)).toBeInTheDocument()
    })

    const demoUserButton = screen.getByText(/system administrator/i).closest('button')
    expect(demoUserButton).toBeInTheDocument()

    await user.click(demoUserButton!)

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement

    expect(emailInput.value).toBe('admin@billing-re.com')
    expect(passwordInput.value).toBe('admin123')
  })
})