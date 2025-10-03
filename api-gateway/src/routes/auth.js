const { z } = require('zod');
const { generateToken, verifyToken, VALID_ROLES } = require('../middleware/auth');

// Validation schemas
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  role: z.enum(VALID_ROLES).optional()
});

const refreshTokenSchema = z.object({
  refreshToken: z.string()
});

// Simulated user database (in production, this would be Supabase)
const DEMO_USERS = {
  'test@test.com': {
    userId: '7a14e8f6-21cf-45e9-a971-d747593a0a76',
    email: 'test@test.com',
    password: '123456', // In production: bcrypt hashed
    role: 'SYSTEM_ADMIN',
    name: 'Test Administrator',
    customerIds: [],
    permissions: { all: true }
  },
  'admin@billing-re.com': {
    userId: '550e8400-e29b-41d4-a716-446655440001',
    email: 'admin@billing-re.com',
    password: 'admin123', // In production: bcrypt hashed
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

async function routes(fastify) {
  // Login endpoint
  fastify.post('/auth/login', {
    schema: {
      description: 'Authenticate user and return JWT token',
      tags: ['Authentication'],
      body: {
        type: 'object',
        properties: {
          email: { type: 'string', format: 'email' },
          password: { type: 'string', minLength: 6 },
          role: { type: 'string', enum: VALID_ROLES }
        },
        required: ['email', 'password']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            token: { type: 'string' },
            user: {
              type: 'object',
              properties: {
                userId: { type: 'string' },
                email: { type: 'string' },
                role: { type: 'string' },
                name: { type: 'string' },
                customerIds: { type: 'array', items: { type: 'string' } },
                permissions: { type: 'object', additionalProperties: true }
              }
            },
            expiresIn: { type: 'string' },
            tokenType: { type: 'string' }
          }
        },
        401: {
          type: 'object',
          properties: {
            error: { type: 'object' }
          }
        }
      }
    }
  }, async (request, reply) => {
    try {
      // Validate input
      const validationResult = loginSchema.safeParse(request.body);
      if (!validationResult.success) {
        return reply.status(400).send({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid login credentials format',
            details: validationResult.error.issues
          }
        });
      }

      const { email, password, role } = validationResult.data;

      // Find user (in production: query Supabase user_profiles table)
      const user = DEMO_USERS[email.toLowerCase()];

      if (!user || user.password !== password) {
        // Log failed attempt (without sensitive data)
        fastify.log.warn({ email, ip: request.ip }, 'Failed login attempt');

        return reply.status(401).send({
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password',
            timestamp: new Date().toISOString()
          }
        });
      }

      // Check role if specified
      if (role && user.role !== role) {
        return reply.status(403).send({
          error: {
            code: 'ROLE_MISMATCH',
            message: `User does not have role: ${role}. User role: ${user.role}`,
            timestamp: new Date().toISOString()
          }
        });
      }

      // Generate JWT token
      const token = generateToken({
        userId: user.userId,
        email: user.email,
        role: user.role,
        customerIds: user.customerIds,
        permissions: user.permissions
      });

      // Log successful login
      fastify.log.info({
        userId: user.userId,
        email: user.email,
        role: user.role,
        ip: request.ip
      }, 'User logged in successfully');

      // Return success response
      return {
        token,
        tokenType: 'Bearer',
        expiresIn: process.env.JWT_EXPIRY || '15m',
        user: {
          userId: user.userId,
          email: user.email,
          role: user.role,
          name: user.name,
          customerIds: user.customerIds,
          permissions: user.permissions
        }
      };

    } catch (error) {
      fastify.log.error({ error: error.message }, 'Login endpoint error');

      return reply.status(500).send({
        error: {
          code: 'LOGIN_ERROR',
          message: 'Internal login error',
          timestamp: new Date().toISOString()
        }
      });
    }
  });

  // Token verification endpoint
  fastify.get('/auth/verify', {
    schema: {
      description: 'Verify JWT token validity',
      tags: ['Authentication'],
      headers: {
        type: 'object',
        properties: {
          authorization: { type: 'string' }
        },
        required: ['authorization']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            valid: { type: 'boolean' },
            user: {
              type: 'object',
              properties: {
                userId: { type: 'string' },
                email: { type: 'string' },
                role: { type: 'string' },
                customerIds: { type: 'array', items: { type: 'string' } },
                permissions: { type: 'object', additionalProperties: true },
                tokenIssuedAt: { type: 'string' },
                tokenExpiresAt: { type: 'string' }
              }
            },
            expiresAt: { type: 'string' },
            message: { type: 'string' }
          }
        }
      }
    },
    preHandler: fastify.authenticate // Uses auth middleware
  }, async (request, reply) => {
    // If we reach here, token is valid (auth middleware passed)
    return {
      valid: true,
      user: request.user,
      expiresAt: request.user.tokenExpiresAt.toISOString(),
      message: 'Token is valid'
    };
  });

  // Logout endpoint (token blacklisting would be implemented here)
  fastify.post('/auth/logout', {
    schema: {
      description: 'Logout user (invalidate token)',
      tags: ['Authentication']
    },
    preHandler: fastify.authenticate
  }, async (request, reply) => {
    // In a full implementation, we would:
    // 1. Add token to blacklist in Redis
    // 2. Clear any session data
    // 3. Log the logout event

    fastify.log.info({
      userId: request.user.userId,
      email: request.user.email
    }, 'User logged out');

    return {
      message: 'Logged out successfully',
      timestamp: new Date().toISOString()
    };
  });

  // User profile endpoint
  fastify.get('/auth/profile', {
    schema: {
      description: 'Get current user profile',
      tags: ['Authentication'],
      response: {
        200: {
          type: 'object',
          properties: {
            user: { type: 'object' }
          }
        }
      }
    },
    preHandler: fastify.authenticate
  }, async (request, reply) => {
    return {
      user: request.user
    };
  });

  // Demo users endpoint (development only)
  if (process.env.NODE_ENV === 'development') {
    fastify.get('/auth/demo-users', {
      schema: {
        description: 'Get demo users for testing (development only)',
        tags: ['Development']
      }
    }, async (request, reply) => {
      const demoUsers = Object.values(DEMO_USERS).map(user => ({
        email: user.email,
        role: user.role,
        name: user.name,
        // Don't expose passwords
        loginHint: 'Password is: [role]123 (e.g., admin123, clerk123)'
      }));

      return {
        demoUsers,
        note: 'These are demo users for development. Use email and password to login.',
        loginEndpoint: '/api/v1/auth/login'
      };
    });
  }
}

module.exports = routes;