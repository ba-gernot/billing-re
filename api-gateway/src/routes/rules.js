const axios = require('axios');

const RATING_SERVICE_URL = process.env.RATING_SERVICE_URL || 'http://localhost:3002';

async function routes(fastify) {
  // Get rules from Excel files via rating service
  fastify.get('/rules/:ruleType', {
    schema: {
      description: 'Get rules from Excel files',
      tags: ['Rules'],
      params: {
        type: 'object',
        properties: {
          ruleType: {
            type: 'string',
            enum: ['weight-class', 'service-determination', 'trip-type', 'tax-calculation', 'waiting-times', 'pricing-main', 'pricing-additional']
          }
        },
        required: ['ruleType']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            rule_type: { type: 'string' },
            file_name: { type: 'string' },
            headers: { type: 'array', items: { type: 'string' } },
            rows: { type: 'array' },
            total_count: { type: 'number' }
          }
        }
      }
    },
    preHandler: fastify.authenticate
  }, async (request, reply) => {
    try {
      const { ruleType } = request.params;

      // Forward request to rating service
      const response = await axios.get(`${RATING_SERVICE_URL}/rules/${ruleType}`, {
        timeout: 10000
      });

      return response.data;
    } catch (error) {
      fastify.log.error({ error: error.message, ruleType: request.params.ruleType }, 'Error fetching rules');

      if (error.response) {
        return reply.status(error.response.status).send(error.response.data);
      }

      return reply.status(500).send({
        error: {
          code: 'RULES_FETCH_ERROR',
          message: 'Failed to fetch rules from service',
          timestamp: new Date().toISOString()
        }
      });
    }
  });
}

module.exports = routes;
