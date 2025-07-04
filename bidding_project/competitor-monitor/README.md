# Competitor Monitor Microservice

A TypeScript microservice that fetches competitor pricing data from the DummyJSON API and stores it in Redis for consumption by the main bidding application.

## Features

- **Automated Data Fetching**: Polls DummyJSON API every 5 minutes
- **Redis Integration**: Pushes competitor prices to `competitor_prices` list
- **Health Monitoring**: HTTP endpoints for health checks and data inspection
- **Robust Error Handling**: With automatic reconnection and graceful shutdown
- **Structured Logging**: Using Winston with multiple log levels
- **TypeScript**: Full type safety and modern async/await patterns

## Architecture

```
DummyJSON API → TypeScript Service → Redis List → Django Application
```

## Data Flow

1. **Fetch**: Retrieves product data from `https://dummyjson.com/products`
2. **Transform**: Maps to standardized `CompetitorPrice` interface
3. **Store**: Pushes to Redis list `competitor_prices` using LPUSH
4. **Maintain**: Trims list to latest 1000 entries to prevent memory issues

## Quick Start

### Development
```bash
cd competitor-monitor
npm install
npm run dev
```

### Production
```bash
npm run build
npm start
```

### Docker
```bash
docker build -t competitor-monitor .
docker run -e REDIS_URL=redis://redis:6379 competitor-monitor
```

## Configuration

Environment variables:
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379)
- `LOG_LEVEL`: Logging level (default: info)
- `PORT`: Health server port (default: 3001)

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service health status and Redis connection info.

### Latest Prices
```bash
GET /prices
```
Returns the 5 most recent competitor prices.

## Data Schema

Each competitor price entry includes:
```typescript
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
```

## Integration with Main App

The Django application can consume competitor prices:

```python
import redis
import json

redis_client = redis.Redis.from_url(settings.REDIS_URL)

# Get latest competitor prices
prices_raw = redis_client.lrange('competitor_prices', 0, 9)
prices = [json.loads(p) for p in prices_raw]

for price in prices:
    print(f"Product: {price['productName']}, Price: ${price['price']}")
```

## Monitoring

- **Health Endpoint**: Monitor service availability
- **Logs**: Structured JSON logs with timestamps
- **Redis Metrics**: List length and connection status
- **Error Tracking**: Automatic error logging and alerting

## Development

### Commands
```bash
npm run dev        # Development with hot reload
npm run build      # Compile TypeScript
npm run lint       # ESLint code checking
npm run test       # Run Jest tests
```

### Testing
```bash
# Unit tests
npm test

# Health check
curl http://localhost:3001/health

# View latest prices
curl http://localhost:3001/prices
```

## Production Considerations

- **Scaling**: Stateless design allows horizontal scaling
- **Rate Limiting**: Respects DummyJSON API limits
- **Memory Management**: Auto-trims Redis list to prevent growth
- **Error Recovery**: Automatic reconnection to Redis
- **Security**: Non-root container user, input validation

## Deployment with Main App

The microservice integrates into the existing Docker Compose setup:

```yaml
services:
  competitor-monitor:
    build: ./competitor-monitor
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
    restart: unless-stopped
```

This provides real-time competitor pricing data to enhance the bidding engine's decision-making capabilities.
