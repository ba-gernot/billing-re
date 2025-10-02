import { NextResponse } from 'next/server'

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export interface ServiceHealth {
  service: string
  status: 'healthy' | 'unhealthy'
  response?: any
  error?: string
}

export interface HealthResponse {
  overall_status: 'healthy' | 'degraded'
  services: ServiceHealth[]
  timestamp: string
}

export async function GET() {
  try {
    // Fetch API Gateway's own health
    const gatewayHealthResponse = await fetch(`${API_GATEWAY_URL}/health`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(5000)
    })
    const gatewayHealth = await gatewayHealthResponse.json()

    // Fetch microservices health
    const servicesHealthResponse = await fetch(`${API_GATEWAY_URL}/health/services`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(5000)
    })
    const servicesHealth = await servicesHealthResponse.json() as HealthResponse

    // Combine API Gateway health with microservices
    const allServices: ServiceHealth[] = [
      {
        service: 'api-gateway',
        status: gatewayHealthResponse.ok ? 'healthy' : 'unhealthy',
        response: gatewayHealth
      },
      ...servicesHealth.services
    ]

    const allHealthy = allServices.every(s => s.status === 'healthy')

    return NextResponse.json({
      overall_status: allHealthy ? 'healthy' : 'degraded',
      services: allServices,
      timestamp: new Date().toISOString()
    }, { status: allHealthy ? 200 : 503 })

  } catch (error) {
    console.error('Health check failed:', error)

    // Return degraded status with error info
    return NextResponse.json({
      overall_status: 'degraded',
      services: [
        {
          service: 'api-gateway',
          status: 'unhealthy',
          error: error instanceof Error ? error.message : 'Unknown error'
        },
        {
          service: 'transformation',
          status: 'unhealthy',
          error: 'Unable to reach API Gateway'
        },
        {
          service: 'rating',
          status: 'unhealthy',
          error: 'Unable to reach API Gateway'
        },
        {
          service: 'billing',
          status: 'unhealthy',
          error: 'Unable to reach API Gateway'
        }
      ],
      timestamp: new Date().toISOString()
    }, { status: 503 })
  }
}
