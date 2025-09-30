'use client'

import { useAuth, hasPermission } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { LogOut, Settings, User, FileText, Database, DollarSign } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export function NavBar() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  if (!user) return null

  return (
    <nav className="border-b bg-white">
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard" className="text-xl font-bold text-gray-900">
            Billing RE
          </Link>
        </div>

        <div className="flex-1 flex justify-center">
          <div className="flex space-x-8">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center space-x-1"
            >
              <DollarSign className="h-4 w-4" />
              <span>Dashboard</span>
            </Link>

            <Link
              href="/orders"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center space-x-1"
            >
              <FileText className="h-4 w-4" />
              <span>Orders</span>
            </Link>

            <Link
              href="/invoices"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center space-x-1"
            >
              <FileText className="h-4 w-4" />
              <span>Invoices</span>
            </Link>

            {hasPermission(user, 'rules') && (
              <Link
                href="/rules"
                className="text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center space-x-1"
              >
                <Database className="h-4 w-4" />
                <span>Rules</span>
              </Link>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-sm">
            <div className="font-medium text-gray-900">{user.name}</div>
            <div className="text-gray-500">{user.role?.replace('_', ' ') || 'User'}</div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <User className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  )
}