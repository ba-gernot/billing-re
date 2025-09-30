import { NextResponse } from 'next/server';

const DEMO_USERS = [
  {
    email: 'test@test.com',
    role: 'SYSTEM_ADMIN',
    name: 'Test Administrator',
    password: '123456',
    loginHint: 'Password: 123456'
  },
  {
    email: 'admin@billing-re.com',
    role: 'SYSTEM_ADMIN',
    name: 'System Administrator',
    password: 'admin123',
    loginHint: 'Password: admin123'
  },
  {
    email: 'clerk@billing-re.com',
    role: 'BILLING_CLERK',
    name: 'Billing Clerk',
    password: 'clerk123',
    loginHint: 'Password: clerk123'
  },
  {
    email: 'manager@billing-re.com',
    role: 'RULE_MANAGER',
    name: 'Rule Manager',
    password: 'manager123',
    loginHint: 'Password: manager123'
  }
];

export async function GET() {
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: { message: 'Demo users only available in development' } },
      { status: 403 }
    );
  }

  return NextResponse.json({
    demoUsers: DEMO_USERS,
    note: 'These are demo users for development. Use email and password to login.',
    loginEndpoint: '/api/v1/auth/login'
  });
}