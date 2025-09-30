'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/lib/auth'
import { authApi } from '@/lib/api'
import { toast } from 'sonner'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  role: z.string().optional(),
})

type LoginForm = z.infer<typeof loginSchema>

interface DemoUser {
  email: string
  role: string
  name: string
  password: string
  loginHint: string
}

export default function LoginPage() {
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { login, isAuthenticated } = useAuth()
  const router = useRouter()

  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      role: '',
    },
  })

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard')
    }

    // Load demo users for development
    const loadDemoUsers = async () => {
      try {
        const response = await authApi.getDemoUsers()
        setDemoUsers(response.demoUsers || [])
      } catch (error) {
        console.error('Failed to load demo users:', error)
      }
    }

    loadDemoUsers()
  }, [isAuthenticated, router])

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      await login(data)
      toast.success('Login successful!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.error?.message || 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  const fillDemoUser = (user: DemoUser) => {
    form.setValue('email', user.email)
    form.setValue('password', user.password)
    form.setValue('role', user.role)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Billing RE System
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Login</CardTitle>
            <CardDescription>
              Enter your credentials to access the billing system
            </CardDescription>
          </CardHeader>

          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  {...form.register('email')}
                />
                {form.formState.errors.email && (
                  <p className="text-sm text-red-600">
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  {...form.register('password')}
                />
                {form.formState.errors.password && (
                  <p className="text-sm text-red-600">
                    {form.formState.errors.password.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Role (Optional)</Label>
                <Input
                  id="role"
                  placeholder="Leave empty for default role"
                  {...form.register('role')}
                />
              </div>
            </CardContent>

            <CardFooter>
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* Demo Users Section */}
        {demoUsers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Demo Users (Development)</CardTitle>
              <CardDescription className="text-xs">
                Click to auto-fill login credentials
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {demoUsers.map((user) => (
                <Button
                  key={user.email}
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => fillDemoUser(user)}
                  type="button"
                >
                  <div className="text-left">
                    <div className="font-medium">{user.name}</div>
                    <div className="text-gray-500">{user.email} - {user.role}</div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}