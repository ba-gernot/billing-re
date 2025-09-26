'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
  fallbackPath?: string
}

export function ProtectedRoute({
  children,
  requiredPermission,
  fallbackPath = '/login'
}: ProtectedRouteProps) {
  const { isAuthenticated, user, verifyToken } = useAuth()
  const router = useRouter()

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated) {
        const isValid = await verifyToken()
        if (!isValid) {
          router.push(fallbackPath)
          return
        }
      }

      if (requiredPermission && user) {
        const hasRequiredPermission = user.permissions[requiredPermission] || user.permissions.all
        if (!hasRequiredPermission) {
          router.push('/unauthorized')
          return
        }
      }
    }

    checkAuth()
  }, [isAuthenticated, user, requiredPermission, router, verifyToken, fallbackPath])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}