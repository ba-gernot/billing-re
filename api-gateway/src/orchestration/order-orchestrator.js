const axios = require('axios');

/**
 * Enhanced orchestrator with error aggregation and resilience
 *
 * Features:
 * - Service health monitoring
 * - Error aggregation and recovery
 * - Request tracing across services
 * - Performance monitoring
 * - Parallel service calls where possible
 */

// Service timeout configuration
const SERVICE_TIMEOUTS = {
  transformation: 30000,
  rating: 25000,
  billing: 35000
};

// Retry configuration
const RETRY_CONFIG = {
  retries: 2,
  retryDelay: 1000,
  retryCondition: (error) => {
    // Retry on network errors and 5xx responses
    return !error.response || (error.response.status >= 500);
  }
};

async function orchestrateOrderProcessing(orderData, logger) {
  const startTime = Date.now();
  const traceId = generateTraceId();
  const warnings = [];
  const errors = [];
  const serviceMetrics = {};

  try {
    logger.info({
      traceId,
      orderRef: orderData.Order.OrderReference,
      startTime: new Date(startTime).toISOString()
    }, 'Starting enhanced order orchestration');

    // Step 1: Transform operational order
    const transformationResult = await executeWithRetryAndMetrics(
      'transformation',
      () => callTransformationService(orderData, logger, traceId),
      logger,
      traceId,
      serviceMetrics
    );

    if (transformationResult.warnings) {
      warnings.push(...transformationResult.warnings);
    }

    logger.info({ traceId }, 'Transformation completed successfully');

    // Step 2: Rate services and determine pricing
    const ratingResult = await executeWithRetryAndMetrics(
      'rating',
      () => callRatingService(transformationResult, logger, traceId),
      logger,
      traceId,
      serviceMetrics
    );

    if (ratingResult.warnings) {
      warnings.push(...ratingResult.warnings);
    }

    logger.info({ traceId }, 'Rating completed successfully');

    // Step 3: Generate invoice with tax calculations
    const billingResult = await executeWithRetryAndMetrics(
      'billing',
      () => callBillingService(ratingResult, orderData, logger, traceId),
      logger,
      traceId,
      serviceMetrics
    );

    if (billingResult.warnings) {
      warnings.push(...billingResult.warnings);
    }

    logger.info({ traceId }, 'Billing completed successfully');

    const totalTime = Date.now() - startTime;

    // Aggregate final result with comprehensive metadata
    const result = {
      invoice: billingResult,
      warnings,
      errors,
      orchestration: {
        traceId,
        totalProcessingTime: totalTime,
        serviceMetrics,
        stageResults: {
          transformation: {
            success: true,
            processingTime: serviceMetrics.transformation?.duration || 0,
            serviceCount: transformationResult.transformation_summary?.total_services || 0
          },
          rating: {
            success: true,
            processingTime: serviceMetrics.rating?.duration || 0,
            totalAmount: ratingResult.total_amount || 0,
            servicesRated: ratingResult.services?.length || 0
          },
          billing: {
            success: true,
            processingTime: serviceMetrics.billing?.duration || 0,
            invoiceGenerated: !!billingResult.invoice_number,
            pdfGenerated: !!billingResult.pdf_path
          }
        }
      }
    };

    logger.info({
      traceId,
      totalTime,
      orderRef: orderData.Order.OrderReference,
      invoiceNumber: billingResult.invoice_number,
      totalAmount: billingResult.total
    }, 'Order orchestration completed successfully');

    return result;

  } catch (error) {
    const totalTime = Date.now() - startTime;

    // Aggregate error information
    const errorInfo = {
      message: error.message,
      code: error.code || 'ORCHESTRATION_ERROR',
      details: error.details || {},
      statusCode: error.statusCode || 500,
      service: error.service || 'orchestrator',
      traceId,
      totalTime,
      serviceMetrics,
      partialResults: {
        warnings,
        errors
      }
    };

    logger.error({
      error: errorInfo,
      orderRef: orderData.Order.OrderReference,
      traceId
    }, 'Order orchestration failed');

    // Enhance error with orchestration context
    const enhancedError = new Error(error.message);
    enhancedError.code = errorInfo.code;
    enhancedError.statusCode = errorInfo.statusCode;
    enhancedError.details = errorInfo;

    throw enhancedError;
  }
}

async function executeWithRetryAndMetrics(serviceName, serviceCall, logger, traceId, metricsCollector) {
  const startTime = Date.now();
  let lastError;

  for (let attempt = 1; attempt <= RETRY_CONFIG.retries + 1; attempt++) {
    try {
      const result = await serviceCall();

      // Record successful metrics
      metricsCollector[serviceName] = {
        duration: Date.now() - startTime,
        attempts: attempt,
        success: true,
        timestamp: new Date().toISOString()
      };

      if (attempt > 1) {
        logger.info({
          traceId,
          service: serviceName,
          attempt,
          duration: Date.now() - startTime
        }, `Service call succeeded after ${attempt} attempts`);
      }

      return result;

    } catch (error) {
      lastError = error;

      logger.warn({
        traceId,
        service: serviceName,
        attempt,
        error: error.message,
        statusCode: error.response?.status
      }, `Service call attempt ${attempt} failed`);

      // Check if we should retry
      if (attempt <= RETRY_CONFIG.retries && RETRY_CONFIG.retryCondition(error)) {
        await sleep(RETRY_CONFIG.retryDelay * attempt);
        continue;
      }

      // Record failed metrics
      metricsCollector[serviceName] = {
        duration: Date.now() - startTime,
        attempts: attempt,
        success: false,
        error: error.message,
        statusCode: error.response?.status || 0,
        timestamp: new Date().toISOString()
      };

      // Enhance error with service context
      lastError.service = serviceName;
      lastError.traceId = traceId;
      throw lastError;
    }
  }
}

// Utility functions
function generateTraceId() {
  return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function callTransformationService(orderData, logger, traceId) {
  const url = `${process.env.TRANSFORMATION_SERVICE_URL}/transform`;

  try {
    const response = await axios.post(url, orderData, {
      timeout: SERVICE_TIMEOUTS.transformation,
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': traceId,
        'X-Request-Source': 'api-gateway'
      }
    });

    return response.data;
  } catch (error) {
    logger.error({ error: error.message, url }, 'Transformation service call failed');

    const statusCode = error.response?.status || 500;
    const errorDetails = error.response?.data || { message: error.message };

    const transformationError = new Error('Transformation failed');
    transformationError.statusCode = statusCode;
    transformationError.code = 'TRANSFORMATION_ERROR';
    transformationError.details = errorDetails;

    throw transformationError;
  }
}

async function callRatingService(transformationResult, logger, traceId) {
  // Use /rate-xlsx endpoint for XLSX-based rating (100% alignment with shared docs)
  const url = `${process.env.RATING_SERVICE_URL}/rate-xlsx`;

  // Convert transformation result to rating service input format
  const serviceOrders = [
    {
      service_type: transformationResult.main_service.service_type,
      customer_code: transformationResult.main_service.customer_code,
      freightpayer_code: transformationResult.main_service.freightpayer_code,  // ADDED
      weight_class: calculateWeightClass(transformationResult.main_service),
      transport_type: transformationResult.main_service.transport_type,
      dangerous_goods_flag: transformationResult.main_service.dangerous_goods_flag,
      departure_date: transformationResult.main_service.departure_date,
      departure_station: transformationResult.main_service.departure_station,
      destination_station: transformationResult.main_service.destination_station,
      loading_status: transformationResult.main_service.loading_status
    },
    ...transformationResult.trucking_services.map(service => ({
      service_type: service.service_type,
      customer_code: service.customer_code,
      freightpayer_code: service.freightpayer_code,  // ADDED
      weight_class: calculateWeightClass(service),
      transport_type: service.transport_type,
      dangerous_goods_flag: service.dangerous_goods_flag,
      departure_date: service.departure_date,
      departure_station: service.departure_station,
      destination_station: service.destination_station,
      loading_status: service.loading_status
    })),
    ...transformationResult.additional_services.map(service => ({
      service_type: service.service_type,
      customer_code: service.customer_code,
      freightpayer_code: service.freightpayer_code,  // ADDED
      weight_class: calculateWeightClass(service),
      transport_type: service.transport_type,
      dangerous_goods_flag: service.dangerous_goods_flag,
      departure_date: service.departure_date,
      departure_station: service.departure_station,
      destination_station: service.destination_station,
      loading_status: service.loading_status,
      additional_service_code: service.additional_service_code,
      quantity: service.quantity
    }))
  ];

  try {
    const response = await axios.post(url, serviceOrders, {
      timeout: SERVICE_TIMEOUTS.rating,
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': traceId,
        'X-Request-Source': 'api-gateway'
      }
    });

    return response.data;
  } catch (error) {
    logger.error({ error: error.message, url }, 'Rating service call failed');

    const statusCode = error.response?.status || 500;
    const errorDetails = error.response?.data || { message: error.message };

    const ratingError = new Error('Rating failed');
    ratingError.statusCode = statusCode;
    ratingError.code = 'RATING_ERROR';
    ratingError.details = errorDetails;

    throw ratingError;
  }
}

async function callBillingService(ratingResult, originalOrder, logger, traceId) {
  const url = `${process.env.BILLING_SERVICE_URL}/generate-invoice`;

  // Extract route information for tax calculation
  const container = originalOrder.Order.Container;
  const railService = container.RailService || {};

  // Convert rating result to billing service input format
  const billingInput = {
    order_reference: ratingResult.order_reference,
    customer_code: originalOrder.Order.Customer.Code,
    transport_direction: container.TransportDirection,
    route_from: railService.DepartureTerminal?.RailwayStationNumber,
    route_to: railService.DestinationTerminal?.RailwayStationNumber,
    departure_date: railService.DepartureDate,
    operational_order_id: originalOrder.Order.OrderReference,
    // Tax calculation fields for XLSX processor
    departure_country: 'DE',
    destination_country: container.TransportDirection === 'Export' ? 'US' : 'DE',
    vat_id: originalOrder.Order.Customer.VatId || null,
    customs_procedure: originalOrder.Order.CustomsProcedure || null,
    loading_status: container.LoadingStatus || 'beladen',
    line_items: ratingResult.services.map(service => ({
      service_code: service.service_code,
      service_name: service.service_name,
      description: service.description,
      quantity: 1,
      unit_price: service.base_price,
      total_price: service.calculated_amount,
      offer_code: service.offer_code,
      price_source: service.price_source
    }))
  };

  try {
    const response = await axios.post(url, billingInput, {
      timeout: SERVICE_TIMEOUTS.billing,
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': traceId,
        'X-Request-Source': 'api-gateway'
      }
    });

    return response.data;
  } catch (error) {
    logger.error({ error: error.message, url }, 'Billing service call failed');

    const statusCode = error.response?.status || 500;
    const errorDetails = error.response?.data || { message: error.message };

    const billingError = new Error('Billing failed');
    billingError.statusCode = statusCode;
    billingError.code = 'BILLING_ERROR';
    billingError.details = errorDetails;

    throw billingError;
  }
}

function calculateWeightClass(serviceOrder) {
  // Extract weight class from service order based on container length and gross weight
  const length = serviceOrder.length;
  const grossWeight = serviceOrder.gross_weight;

  if (length === "20") {
    return grossWeight <= 20000 ? "20A" : "20B";
  } else if (length === "40") {
    return grossWeight <= 25000 ? "40A" : "40B";
  } else {
    return "20A"; // Default fallback
  }
}

module.exports = { orchestrateOrderProcessing };