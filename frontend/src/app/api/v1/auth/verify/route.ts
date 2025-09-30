import { NextRequest, NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'

export async function GET(request: NextRequest) {
  console.log('=== TOKEN VERIFICATION API ROUTE CALLED ===')

  try {
    // Get token from Authorization header
    const authHeader = request.headers.get('authorization')

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('No valid authorization header found')
      return NextResponse.json(
        {
          valid: false,
          error: { code: 'NO_TOKEN', message: 'No authorization token provided' }
        },
        { status: 401 }
      )
    }

    const token = authHeader.substring(7) // Remove 'Bearer ' prefix

    // Verify token
    const secret = process.env.JWT_SECRET || 'dev-secret-key-change-in-production'

    try {
      const decoded = jwt.verify(token, secret) as any

      console.log('Token verified successfully for user:', decoded.email)

      // Return user data from token
      return NextResponse.json({
        valid: true,
        user: {
          userId: decoded.userId,
          email: decoded.email,
          role: decoded.role,
          name: decoded.name || 'User',
          customerIds: decoded.customerIds || [],
          permissions: decoded.permissions || { all: true }
        }
      })
    } catch (verifyError: any) {
      console.log('Token verification failed:', verifyError.message)

      // Determine specific error type
      if (verifyError.name === 'TokenExpiredError') {
        return NextResponse.json(
          {
            valid: false,
            error: { code: 'TOKEN_EXPIRED', message: 'Token has expired' }
          },
          { status: 401 }
        )
      } else if (verifyError.name === 'JsonWebTokenError') {
        return NextResponse.json(
          {
            valid: false,
            error: { code: 'INVALID_TOKEN', message: 'Invalid token' }
          },
          { status: 401 }
        )
      } else {
        return NextResponse.json(
          {
            valid: false,
            error: { code: 'VERIFICATION_ERROR', message: 'Token verification failed' }
          },
          { status: 401 }
        )
      }
    }
  } catch (error: any) {
    console.error('Verification error:', error)
    return NextResponse.json(
      {
        valid: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error' }
      },
      { status: 500 }
    )
  }
}