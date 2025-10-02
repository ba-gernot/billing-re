const { z } = require('zod');
const { orchestrateOrderProcessing } = require('../orchestration/order-orchestrator');

// Validation schemas
const orderSchema = z.object({
  Order: z.object({
    OrderReference: z.string(),
    Customer: z.object({
      Code: z.string(),
      Name: z.string().optional()
    }),
    Freightpayer: z.object({
      Code: z.string(),
      Name: z.string().optional()
    }),
    Consignee: z.object({
      Code: z.string(),
      Name: z.string().optional()
    }),
    Container: z.object({
      Position: z.string(),
      ContainerTypeIsoCode: z.string(),
      TareWeight: z.string(),
      Payload: z.string(),
      TransportDirection: z.enum(['Export', 'Import', 'Domestic']),
      DangerousGoodFlag: z.enum(['J', 'N']),
      TakeOver: z.object({
        DepartureCountryIsoCode: z.string()
      }).optional(),
      HandOver: z.object({
        DestinationCountryIsoCode: z.string()
      }).optional(),
      RailService: z.object({
        DepartureDate: z.string(),
        DepartureTerminal: z.object({
          RailwayStationNumber: z.string()
        }),
        DestinationTerminal: z.object({
          RailwayStationNumber: z.string()
        })
      }),
      TruckingServices: z.array(z.any()).optional(),
      AdditionalServices: z.array(z.any()).optional()
    })
  })
});

async function routes(fastify) {
  // Main order processing endpoint
  fastify.post('/process-order', {
    schema: {
      description: 'Process operational order through complete billing pipeline',
      tags: ['Orders'],
      body: {
        type: 'object',
        properties: {
          Order: { type: 'object' }
        },
        required: ['Order']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            invoice: {
              type: 'object',
              additionalProperties: true  // Allow all invoice properties
            },
            processing_time_ms: { type: 'number' },
            warnings: { type: 'array' },
            request_id: { type: 'string' }
          }
        }
      }
    },
    preHandler: fastify.rateLimit({
      max: 50,
      timeWindow: 60000
    })
  }, async (request, reply) => {
    const startTime = Date.now();

    try {
      // Validate input
      const validationResult = orderSchema.safeParse(request.body);
      if (!validationResult.success) {
        return reply.status(400).send({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid order format',
            details: validationResult.error.issues
          }
        });
      }

      // Orchestrate processing through all services
      const result = await orchestrateOrderProcessing(validationResult.data, fastify.log);

      const processingTime = Date.now() - startTime;

      return {
        invoice: result.invoice,
        processing_time_ms: processingTime,
        warnings: result.warnings || [],
        request_id: request.id
      };

    } catch (error) {
      fastify.log.error({ error, body: request.body }, 'Order processing failed');

      const statusCode = error.statusCode || 500;
      return reply.status(statusCode).send({
        error: {
          code: error.code || 'PROCESSING_ERROR',
          message: error.message || 'Order processing failed',
          ...(error.details && { details: error.details })
        }
      });
    }
  });

  // Health check for order processing
  fastify.get('/process-order/health', async (request, reply) => {
    return {
      endpoint: '/api/v1/process-order',
      status: 'available',
      rate_limit: {
        max_requests: 50,
        window_ms: 60000
      }
    };
  });
}

module.exports = routes;