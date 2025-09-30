import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

// Demo users for development
const DEMO_USERS: Record<string, any> = {
  'test@test.com': {
    userId: '7a14e8f6-21cf-45e9-a971-d747593a0a76',
    email: 'test@test.com',
    password: '123456',
    role: 'SYSTEM_ADMIN',
    name: 'Test Administrator',
    customerIds: [],
    permissions: { all: true }
  },
  'admin@billing-re.com': {
    userId: '550e8400-e29b-41d4-a716-446655440001',
    email: 'admin@billing-re.com',
    password: 'admin123',
    role: 'SYSTEM_ADMIN',
    name: 'System Administrator',
    customerIds: [],
    permissions: { all: true }
  },
  'clerk@billing-re.com': {
    userId: '550e8400-e29b-41d4-a716-446655440002',
    email: 'clerk@billing-re.com',
    password: 'clerk123',
    role: 'BILLING_CLERK',
    name: 'Billing Clerk',
    customerIds: ['123456', '234567'],
    permissions: { billing: true, orders: true }
  },
  'manager@billing-re.com': {
    userId: '550e8400-e29b-41d4-a716-446655440003',
    email: 'manager@billing-re.com',
    password: 'manager123',
    role: 'RULE_MANAGER',
    name: 'Rule Manager',
    customerIds: [],
    permissions: { rules: true, pricing: true }
  }
};

function generateToken(payload: any): string {
  // Simple JWT-like token for demo (use proper JWT library in production)
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const body = Buffer.from(JSON.stringify({
    ...payload,
    iat: Date.now(),
    exp: Date.now() + (15 * 60 * 1000) // 15 minutes
  })).toString('base64url');

  const secret = process.env.JWT_SECRET || 'dev-secret-key';
  const signature = crypto
    .createHmac('sha256', secret)
    .update(`${header}.${body}`)
    .digest('base64url');

  return `${header}.${body}.${signature}`;
}

export async function POST(request: NextRequest) {
  console.log('=== LOGIN API ROUTE CALLED ===');
  console.log('Request URL:', request.url);
  console.log('Request method:', request.method);

  try {
    const body = await request.json();
    console.log('Request body:', body);
    const { email, password } = body;

    if (!email || !password) {
      console.log('Validation error: missing email or password');
      return NextResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Email and password are required' } },
        { status: 400 }
      );
    }

    // Check demo users
    console.log('Looking for user:', email.toLowerCase());
    console.log('Available users:', Object.keys(DEMO_USERS));
    const demoUser = DEMO_USERS[email.toLowerCase()];

    if (!demoUser) {
      console.log('User not found:', email);
      return NextResponse.json(
        { error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    console.log('User found, checking password...');
    if (demoUser.password !== password) {
      console.log('Password mismatch. Expected:', demoUser.password, 'Got:', password);
      return NextResponse.json(
        { error: { code: 'INVALID_CREDENTIALS', message: 'Invalid email or password' } },
        { status: 401 }
      );
    }

    console.log('Login successful for:', email);

    // Generate token
    const token = generateToken({
      userId: demoUser.userId,
      email: demoUser.email,
      role: demoUser.role,
      customerIds: demoUser.customerIds || [],
      permissions: demoUser.permissions || { all: true }
    });

    return NextResponse.json({
      token,
      tokenType: 'Bearer',
      expiresIn: '15m',
      user: {
        userId: demoUser.userId,
        email: demoUser.email,
        role: demoUser.role,
        name: demoUser.name || 'User',
        customerIds: demoUser.customerIds || [],
        permissions: demoUser.permissions || { all: true }
      }
    });

  } catch (error: any) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: { code: 'LOGIN_ERROR', message: 'Internal login error' } },
      { status: 500 }
    );
  }
}