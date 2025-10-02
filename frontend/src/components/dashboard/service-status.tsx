import { Loader2 } from 'lucide-react'

interface ServiceStatusProps {
  name: string
  status: 'healthy' | 'unhealthy' | 'loading'
  displayName?: string
}

const statusConfig = {
  healthy: {
    color: 'bg-green-500',
    textColor: 'text-green-600',
    label: 'Online'
  },
  unhealthy: {
    color: 'bg-red-500',
    textColor: 'text-red-600',
    label: 'Offline'
  },
  loading: {
    color: 'bg-gray-400',
    textColor: 'text-gray-600',
    label: 'Loading...'
  }
}

export function ServiceStatus({ name, status, displayName }: ServiceStatusProps) {
  const config = statusConfig[status]
  const label = displayName || name.charAt(0).toUpperCase() + name.slice(1) + ' Service'

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium">{label}</span>
      <div className="flex items-center space-x-2">
        {status === 'loading' ? (
          <Loader2 className="h-3 w-3 animate-spin text-gray-400" />
        ) : (
          <div className={`h-2 w-2 rounded-full ${config.color}`} />
        )}
        <span className={`text-sm ${config.textColor}`}>
          {config.label}
        </span>
      </div>
    </div>
  )
}
