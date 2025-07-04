/**
 * Competitor Monitor Microservice
 * 
 * Fetches competitor product data from DummyJSON API and pushes pricing
 * information to Redis list for consumption by the main bidding application.
 */
import axios from 'axios';
import { createClient, RedisClientType } from 'redis';
import * as cron from 'node-cron';
import winston from 'winston';

// Types
interface Product {
  id: number;
  title: string;
  price: number;
  brand: string;
  category: string;
  discountPercentage: number;
  rating: number;
  stock: number;
}

interface DummyJsonResponse {
  products: Product[];
  total: number;
  skip: number;
  limit: number;
}

interface CompetitorPrice {
  productId: number;
  productName: string;
  brand: string;
  category: string;
  price: number;
  discountPercentage: number;
  rating: number;
  stock: number;
  timestamp: string;
  source: 'dummyjson';
}

class CompetitorMonitor {
  private redis: RedisClientType;
  private logger: winston.Logger;
  private readonly REDIS_LIST_KEY = 'competitor_prices';
  private readonly API_URL = 'https://dummyjson.com/products';
  private readonly FETCH_INTERVAL = '*/5 * * * *'; // Every 5 minutes

  constructor() {
    // Initialize Redis client
    this.redis = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      socket: {
        reconnectStrategy: (retries) => Math.min(retries * 50, 500)
      }
    });

    // Initialize logger
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'competitor-monitor' },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({ 
          filename: 'logs/error.log', 
          level: 'error' 
        }),
        new winston.transports.File({ 
          filename: 'logs/combined.log' 
        })
      ]
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.redis.on('error', (err) => {
      this.logger.error('Redis Client Error:', err);
    });

    this.redis.on('connect', () => {
      this.logger.info('Connected to Redis');
    });

    this.redis.on('reconnecting', () => {
      this.logger.warn('Reconnecting to Redis...');
    });

    process.on('SIGTERM', () => this.gracefulShutdown());
    process.on('SIGINT', () => this.gracefulShutdown());
  }

  public async start(): Promise<void> {
    try {
      await this.redis.connect();
      this.logger.info('Competitor Monitor started successfully');
      
      // Run initial fetch
      await this.fetchAndStoreCompetitorPrices();
      
      // Schedule periodic fetches
      cron.schedule(this.FETCH_INTERVAL, async () => {
        await this.fetchAndStoreCompetitorPrices();
      });
      
      this.logger.info(`Scheduled competitor price fetching every 5 minutes`);
      
    } catch (error) {
      this.logger.error('Failed to start competitor monitor:', error);
      process.exit(1);
    }
  }

  private async fetchAndStoreCompetitorPrices(): Promise<void> {
    try {
      this.logger.info('Fetching competitor prices from DummyJSON API...');
      
      const response = await axios.get<DummyJsonResponse>(this.API_URL, {
        params: {
          limit: 30,
          skip: 0
        },
        timeout: 10000
      });

      if (!response.data || !response.data.products) {
        throw new Error('Invalid response structure from DummyJSON API');
      }

      const competitorPrices: CompetitorPrice[] = response.data.products.map(product => ({
        productId: product.id,
        productName: product.title,
        brand: product.brand,
        category: product.category,
        price: product.price,
        discountPercentage: product.discountPercentage,
        rating: product.rating,
        stock: product.stock,
        timestamp: new Date().toISOString(),
        source: 'dummyjson'
      }));

      // Store prices in Redis list
      await this.storePricesInRedis(competitorPrices);
      
      this.logger.info(`Successfully fetched and stored ${competitorPrices.length} competitor prices`);
      
      // Log sample data for debugging
      if (competitorPrices.length > 0) {
        this.logger.debug('Sample competitor price:', competitorPrices[0]);
      }

    } catch (error) {
      this.logger.error('Error fetching competitor prices:', error);
      
      if (axios.isAxiosError(error)) {
        this.logger.error('API Error Details:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          url: error.config?.url
        });
      }
    }
  }

  private async storePricesInRedis(prices: CompetitorPrice[]): Promise<void> {
    try {
      const serializedPrices = prices.map(price => JSON.stringify(price));
      
      // Use LPUSH to add to the beginning of the list
      await this.redis.lPush(this.REDIS_LIST_KEY, serializedPrices);
      
      // Trim the list to keep only the latest 1000 entries to prevent memory issues
      await this.redis.lTrim(this.REDIS_LIST_KEY, 0, 999);
      
      const listLength = await this.redis.lLen(this.REDIS_LIST_KEY);
      this.logger.info(`Stored competitor prices. Current list length: ${listLength}`);
      
    } catch (error) {
      this.logger.error('Error storing prices in Redis:', error);
      throw error;
    }
  }

  public async getLatestPrices(count: number = 10): Promise<CompetitorPrice[]> {
    try {
      const serializedPrices = await this.redis.lRange(this.REDIS_LIST_KEY, 0, count - 1);
      return serializedPrices.map(price => JSON.parse(price) as CompetitorPrice);
    } catch (error) {
      this.logger.error('Error retrieving prices from Redis:', error);
      throw error;
    }
  }

  public async getHealthStatus(): Promise<{ status: string; redis: string; lastFetch: string }> {
    try {
      await this.redis.ping();
      const listLength = await this.redis.lLen(this.REDIS_LIST_KEY);
      
      return {
        status: 'healthy',
        redis: 'connected',
        lastFetch: `${listLength} prices in cache`
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        redis: 'disconnected',
        lastFetch: 'unknown'
      };
    }
  }

  private async gracefulShutdown(): Promise<void> {
    this.logger.info('Graceful shutdown initiated...');
    
    try {
      await this.redis.quit();
      this.logger.info('Redis connection closed');
      process.exit(0);
    } catch (error) {
      this.logger.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// HTTP Health Check Server (optional for monitoring)
import http from 'http';

function startHealthServer(monitor: CompetitorMonitor): void {
  const server = http.createServer(async (req, res) => {
    if (req.url === '/health') {
      try {
        const health = await monitor.getHealthStatus();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(health));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'error', message: error }));
      }
    } else if (req.url === '/prices') {
      try {
        const prices = await monitor.getLatestPrices(5);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ prices, count: prices.length }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'error', message: error }));
      }
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ message: 'Not found' }));
    }
  });

  const port = process.env.PORT || 3001;
  server.listen(port, () => {
    console.log(`Health server running on port ${port}`);
  });
}

// Main execution
if (require.main === module) {
  const monitor = new CompetitorMonitor();
  
  // Create logs directory
  const fs = require('fs');
  if (!fs.existsSync('logs')) {
    fs.mkdirSync('logs');
  }
  
  monitor.start().catch(console.error);
  startHealthServer(monitor);
}

export default CompetitorMonitor;
