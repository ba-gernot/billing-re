import { useState, useEffect, useCallback } from 'react'

interface ServiceHealth {
  service: string
  status: 'healthy' | 'unhealthy'
  response?: any
  error?: string
}

interface HealthResponse {
  overall_status: 'healthy' | 'degraded'
  services: ServiceHealth[]
  timestamp: string
}

interface UseServiceHealthReturn {
  health: HealthResponse | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useServiceHealth(
  refreshInterval: number = 30000 // 30 seconds default
): UseServiceHealthReturn {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch('/api/health', {
        cache: 'no-store'
      })

      const data = await response.json()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status')
      console.error('Health check error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Initial fetch
    fetchHealth()

    // Set up interval for auto-refresh
    const interval = setInterval(fetchHealth, refreshInterval)

    // Cleanup on unmount
    return () => clearInterval(interval)
  }, [fetchHealth, refreshInterval])

  return {
    health,
    isLoading,
    error,
    refetch: fetchHealth
  }
}
