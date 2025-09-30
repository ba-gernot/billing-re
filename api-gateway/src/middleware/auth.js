const jwt = require('jsonwebtoken');

/**
 * JWT Authentication Middleware for API Gateway
 *
 * Implements security requirements from roadmap:
 * - JWT 15-minute expiry
 * - RBAC roles: RULE_MANAGER, BILLING_CLERK, SYSTEM_ADMIN
 * - Rate limiting integration
 */

const JWT_SECRET = process.env.JWT_SECRET || 'your-jwt-secret-key';
const JWT_EXPIRY = process.env.JWT_EXPIRY || '15m';

// Valid user roles from roadmap security requirements
const VALID_ROLES = ['SYSTEM_ADMIN', 'BILLING_CLERK', 'RULE_MANAGER', 'READONLY_USER'];

// Protected routes configuration
const PROTECTED_ROUTES = {
  '/api/v1/process-order': ['SYSTEM_ADMIN', 'BILLING_CLERK'],
  '/api/v1/rules': ['SYSTEM_ADMIN', 'RULE_MANAGER'],
  '/api/v1/admin': ['SYSTEM_ADMIN']
};

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/health',
  '/health/services',
  '/api/v1/auth/login',
  '/api/v1/auth/demo-users'
];

async function authMiddleware(request, reply) {
  const { url, method } = request;

  // Skip authentication for public routes
  if (PUBLIC_ROUTES.some(route => url.startsWith(route))) {
    return;
  }

  // Skip authentication for health checks
  if (url === '/health' || url.startsWith('/health/')) {
    return;
  }

  try {
    // Extract JWT token from Authorization header
    const authHeader = request.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.status(401).send({
        error: {
          code: 'MISSING_TOKEN',
          message: 'Authorization header with Bearer token required',
          timestamp: new Date().toISOString()
        }
      });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify JWT token
    let decoded;
    try {
      decoded = jwt.verify(token, JWT_SECRET);
    } catch (jwtError) {
      const errorCode = jwtError.name === 'TokenExpiredError' ? 'TOKEN_EXPIRED' : 'INVALID_TOKEN';

      return reply.status(401).send({
        error: {
          code: errorCode,
          message: jwtError.message,
          timestamp: new Date().toISOString()
        }
      });
    }

    // Validate token payload
    if (!decoded.userId || !decoded.role || !decoded.email) {
      return reply.status(401).send({
        error: {
          code: 'INVALID_TOKEN_PAYLOAD',
          message: 'Token missing required fields (userId, role, email)',
          timestamp: new Date().toISOString()
        }
      });
    }

    // Validate role
    if (!VALID_ROLES.includes(decoded.role)) {
      return reply.status(403).send({
        error: {
          code: 'INVALID_ROLE',
          message: `Invalid role: ${decoded.role}. Valid roles: ${VALID_ROLES.join(', ')}`,
          timestamp: new Date().toISOString()
        }
      });
    }

    // Check route-specific permissions
    const requiredRoles = getRequiredRoles(url);
    if (requiredRoles && !requiredRoles.includes(decoded.role)) {
      return reply.status(403).send({
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: `Access denied. Required roles: ${requiredRoles.join(', ')}. Your role: ${decoded.role}`,
          timestamp: new Date().toISOString(),
          requiredRoles,
          userRole: decoded.role
        }
      });
    }

    // Add user context to request for downstream services
    request.user = {
      userId: decoded.userId,
      email: decoded.email,
      role: decoded.role,
      customerIds: decoded.customerIds || [],
      permissions: decoded.permissions || {},
      tokenIssuedAt: new Date(decoded.iat * 1000),
      tokenExpiresAt: new Date(decoded.exp * 1000)
    };

    // Log successful authentication (without sensitive data)
    request.log.info({
      userId: decoded.userId,
      role: decoded.role,
      url: url,
      method: method
    }, 'User authenticated successfully');

  } catch (error) {
    request.log.error({ error: error.message, url }, 'Authentication middleware error');

    return reply.status(500).send({
      error: {
        code: 'AUTH_MIDDLEWARE_ERROR',
        message: 'Internal authentication error',
        timestamp: new Date().toISOString()
      }
    });
  }
}

function getRequiredRoles(url) {
  // Find matching protected route
  for (const [route, roles] of Object.entries(PROTECTED_ROUTES)) {
    if (url.startsWith(route)) {
      return roles;
    }
  }

  // Default: any authenticated user can access
  return null;
}

/**
 * Generate JWT token for login
 */
function generateToken(userPayload) {
  const payload = {
    userId: userPayload.userId,
    email: userPayload.email,
    role: userPayload.role,
    customerIds: userPayload.customerIds || [],
    permissions: userPayload.permissions || {},
    iat: Math.floor(Date.now() / 1000)
  };

  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRY,
    issuer: 'billing-re-system',
    audience: 'billing-re-api'
  });
}

/**
 * Verify and decode token (for internal use)
 */
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    throw new Error(`Token verification failed: ${error.message}`);
  }
}

/**
 * Check if user has specific permission
 */
function hasPermission(userRole, requiredRoles) {
  if (!requiredRoles || requiredRoles.length === 0) {
    return true; // No specific roles required
  }

  return requiredRoles.includes(userRole);
}

/**
 * Middleware for role-based access control
 */
function requireRole(...roles) {
  return async function(request, reply) {
    if (!request.user) {
      return reply.status(401).send({
        error: {
          code: 'AUTHENTICATION_REQUIRED',
          message: 'User must be authenticated',
          timestamp: new Date().toISOString()
        }
      });
    }

    if (!hasPermission(request.user.role, roles)) {
      return reply.status(403).send({
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: `Access denied. Required roles: ${roles.join(', ')}. Your role: ${request.user.role}`,
          timestamp: new Date().toISOString(),
          requiredRoles: roles,
          userRole: request.user.role
        }
      });
    }
  };
}

module.exports = {
  authMiddleware,
  generateToken,
  verifyToken,
  hasPermission,
  requireRole,
  VALID_ROLES,
  PUBLIC_ROUTES
};