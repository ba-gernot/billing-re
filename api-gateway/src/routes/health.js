async function routes(fastify) {
  fastify.get('/health', async (request, reply) => {
    return {
      status: 'healthy',
      service: 'api-gateway',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0'
    };
  });

  fastify.get('/health/services', async (request, reply) => {
    const axios = require('axios');
    const services = [
      { name: 'transformation', url: process.env.TRANSFORMATION_SERVICE_URL },
      { name: 'rating', url: process.env.RATING_SERVICE_URL },
      { name: 'billing', url: process.env.BILLING_SERVICE_URL }
    ];

    const healthChecks = await Promise.allSettled(
      services.map(async (service) => {
        try {
          const response = await axios.get(`${service.url}/health`, { timeout: 5000 });
          return { name: service.name, status: 'healthy', response: response.data };
        } catch (error) {
          return { name: service.name, status: 'unhealthy', error: error.message };
        }
      })
    );

    const results = healthChecks.map((result, index) => ({
      service: services[index].name,
      ...result.value
    }));

    const allHealthy = results.every(r => r.status === 'healthy');

    reply.status(allHealthy ? 200 : 503).send({
      overall_status: allHealthy ? 'healthy' : 'degraded',
      services: results,
      timestamp: new Date().toISOString()
    });
  });
}

module.exports = routes;