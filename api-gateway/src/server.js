const fastify = require('fastify')({
  logger: {
    level: process.env.LOG_LEVEL || 'info'
  }
});

// Register plugins
fastify.register(require('@fastify/cors'), {
  origin: true,
  credentials: true
});

fastify.register(require('@fastify/jwt'), {
  secret: process.env.JWT_SECRET || 'your-jwt-secret-key'
});

fastify.register(require('@fastify/rate-limit'), {
  max: parseInt(process.env.RATE_LIMIT_REQUESTS) || 100,
  timeWindow: parseInt(process.env.RATE_LIMIT_WINDOW) || 60000
});

// Register authentication middleware
const { authMiddleware } = require('./middleware/auth');
fastify.addHook('preHandler', authMiddleware);

// Add authentication decorator
fastify.decorate('authenticate', authMiddleware);

// Register routes
fastify.register(require('./routes/health'));
fastify.register(require('./routes/auth'), { prefix: '/api/v1' });
fastify.register(require('./routes/orders'), { prefix: '/api/v1' });

// Global error handler
fastify.setErrorHandler(async (error, request, reply) => {
  fastify.log.error(error);

  const statusCode = error.statusCode || 500;
  const response = {
    error: {
      code: error.code || 'INTERNAL_ERROR',
      message: error.message || 'Internal server error',
      ...(error.details && { details: error.details })
    },
    timestamp: new Date().toISOString(),
    requestId: request.id
  };

  reply.status(statusCode).send(response);
});

// Start server
const start = async () => {
  try {
    const port = process.env.PORT || 3000;
    const host = process.env.HOST || '0.0.0.0';

    await fastify.listen({ port, host });
    fastify.log.info(`API Gateway listening on ${host}:${port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();