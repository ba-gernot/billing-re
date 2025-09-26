'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'

export default function Home() {
  const { isAuthenticated, verifyToken } = useAuth()
  const router = useRouter()

  useEffect(() => {
    const checkAuthAndRedirect = async () => {
      if (isAuthenticated) {
        router.push('/dashboard')
      } else {
        const isValid = await verifyToken()
        if (isValid) {
          router.push('/dashboard')
        } else {
          router.push('/login')
        }
      }
    }

    checkAuthAndRedirect()
  }, [isAuthenticated, router, verifyToken])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-600">Loading Billing RE System...</p>
      </div>
    </div>
  )
}
