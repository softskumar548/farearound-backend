# FareAround Backend API

A FastAPI-based backend service for searching flights and hotels using the Amadeus API. This service provides a clean REST API with intelligent caching, retry mechanisms, and token management.

> 📚 **New to this project?** Check out the [Quick Start Guide](QUICKSTART.md) or browse the [Documentation Index](DOCS_INDEX.md) to find what you need.

## Overview

FareAround is a travel search backend that integrates with the Amadeus Travel API to provide:
- Flight search with flexible filtering options
- Hotel search by city and dates
- Affiliate tracking capabilities
- Intelligent caching to reduce API calls
- Automatic token management with OAuth2

## Features

### Core Functionality
- **Flight Search**: Search for flights between cities with support for:
  - Origin and destination (IATA codes)
  - Departure dates
  - Number of adult passengers
  - Non-stop flight filtering
  - Currency selection (default: INR)
  - Configurable result limits

- **Hotel Search**: Find hotel offers by:
  - City code
  - Check-in and check-out dates

- **Affiliate Integration**: Track affiliate information for monetization

### Technical Features
- **Automatic Token Management**: OAuth2 client credentials flow with intelligent token caching
- **Response Caching**: TTL-based in-memory cache to reduce duplicate API calls
- **Retry Logic**: Exponential backoff for network errors and 5xx responses
- **Rate Limit Handling**: Respects 429 responses and Retry-After headers
- **CORS Support**: Configured for cross-origin requests
- **Health Check Endpoint**: Simple health monitoring

## Architecture

### Project Structure

```
farearound-backend/
├── app/
│   ├── api/
│   │   ├── amadeus_client.py    # Amadeus API client with caching and retries
│   │   └── routes.py            # API route definitions
│   ├── core/
│   │   └── config.py            # Configuration and settings management
│   └── main.py                  # FastAPI application entry point
├── tools/
│   ├── test_amadeus_token.py    # Diagnostic tool for token acquisition
│   └── test_search_flights.py   # End-to-end flight search test
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
└── requirements.txt             # Python dependencies

```

### Key Components

#### 1. Amadeus Client (`app/api/amadeus_client.py`)
- Handles all communication with Amadeus API
- Implements OAuth2 token management with automatic refresh
- Provides TTL-based response caching (60s default, 512 items max)
- Retry logic with exponential backoff for reliability
- Thread-safe implementation for concurrent requests

#### 2. API Routes (`app/api/routes.py`)
- `/api/search/flights`: Flight search endpoint
- `/api/search/hotels`: Hotel search endpoint
- `/api/affiliate/info`: Affiliate information retrieval
- `/health`: Health check endpoint

#### 3. Configuration (`app/core/config.py`)
- Environment-based configuration using pydantic
- Support for both pydantic v1 and v2
- Secure credential management via environment variables

#### 4. Main Application (`app/main.py`)
- FastAPI application setup
- CORS middleware configuration
- Startup logging and validation

## Setup and Installation

### Prerequisites
- Python 3.9 or higher
- Amadeus API credentials (from [Amadeus for Developers](https://developers.amadeus.com/))

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd farearound-backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Amadeus credentials:
   ```env
   AMADEUS_CLIENT_ID=your_actual_client_id
   AMADEUS_CLIENT_SECRET=your_actual_client_secret
   AMADEUS_BASE_URL=https://test.api.amadeus.com  # or production URL
   AFFILIATE_ID=your_affiliate_id
   DOMAIN=yourdomain.com
   PORT=8000
   ```

### Running the Application

#### Development Mode
```bash
uvicorn app.main:app --reload --port 8000
```

#### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Reference

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "ok"
}
```

### Search Flights
```http
GET /api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=1&nonStop=false&max=20
```

**Query Parameters**:
- `origin` (required): Origin airport IATA code (3 letters, e.g., "BLR")
- `destination` (required): Destination airport IATA code (3 letters, e.g., "DXB")
- `departureDate` (required): Departure date in YYYY-MM-DD format
- `adults` (optional): Number of adult passengers (1-9, default: 1)
- `nonStop` (optional): Filter for non-stop flights only (default: false)
- `max` (optional): Maximum number of results (1-50, default: 20)

**Response**:
```json
{
  "query": {
    "origin": "BLR",
    "destination": "DXB",
    "departureDate": "2026-04-30",
    "adults": 1,
    "nonStop": false
  },
  "count": 10,
  "offers": [
    {
      "id": "1",
      "total": "25000.00",
      "currency": "INR",
      "duration": "PT4H30M",
      "segments": [
        {
          "from": "BLR",
          "to": "DXB",
          "departAt": "2026-04-30T10:00:00",
          "arriveAt": "2026-04-30T12:30:00",
          "carrier": "EK",
          "flightNumber": "568",
          "segmentDuration": "PT4H30M"
        }
      ]
    }
  ]
}
```

### Search Hotels
```http
GET /api/search/hotels?cityCode=DEL&checkIn=2026-05-01&checkOut=2026-05-05
```

**Query Parameters**:
- `cityCode` (required): City IATA code
- `checkIn` (required): Check-in date (YYYY-MM-DD)
- `checkOut` (required): Check-out date (YYYY-MM-DD)

**Response**: Returns Amadeus hotel search API response

### Affiliate Information
```http
GET /api/affiliate/info
```

**Response**:
```json
{
  "affiliate_id": "your_affiliate_id",
  "domain": "yourdomain.com"
}
```

## Testing

### Diagnostic Tools

The `tools/` directory contains utility scripts for testing:

#### Test Token Acquisition
```bash
python tools/test_amadeus_token.py
```
This script verifies that your Amadeus credentials are working and can acquire an access token.

#### Test Flight Search
```bash
python tools/test_search_flights.py
```
This script performs an end-to-end test of the flight search functionality, including:
- Amadeus API integration
- Response normalization
- Data transformation

### Manual Testing

You can test the API using curl:

```bash
# Health check
curl http://localhost:8000/health

# Flight search
curl "http://localhost:8000/api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=1"

# Hotel search
curl "http://localhost:8000/api/search/hotels?cityCode=DEL&checkIn=2026-05-01&checkOut=2026-05-05"

# Affiliate info
curl http://localhost:8000/api/affiliate/info
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AMADEUS_CLIENT_ID` | Yes | - | Your Amadeus API client ID |
| `AMADEUS_CLIENT_SECRET` | Yes | - | Your Amadeus API client secret |
| `AMADEUS_BASE_URL` | No | `https://test.api.amadeus.com` | Amadeus API base URL (test or production) |
| `AFFILIATE_ID` | No | None | Your affiliate tracking ID |
| `DOMAIN` | No | None | Your domain name |
| `PORT` | No | 8000 | Server port number |

### Caching Configuration

The application uses in-memory TTL caching with the following defaults:
- **Response Cache TTL**: 60 seconds
- **Response Cache Max Size**: 512 entries
- **Token Cache**: Automatic based on `expires_in` from Amadeus (typically 30 minutes)

These are configured in `app/api/amadeus_client.py` and can be adjusted as needed.

## Design Decisions

### Why Custom Amadeus Client?

Instead of using the official Amadeus Python SDK, this project implements a custom client for several reasons:

1. **Lightweight**: No heavy dependencies, just `httpx` for HTTP requests
2. **Transparent Caching**: Built-in TTL cache reduces redundant API calls
3. **Better Retry Logic**: Custom exponential backoff and rate limit handling
4. **Token Management**: Intelligent token caching with automatic refresh
5. **Thread Safety**: Designed for concurrent request handling
6. **Flexibility**: Easy to customize and extend for specific needs

### Pydantic Version Compatibility

The configuration module supports both Pydantic v1 and v2 to ensure compatibility across different environments:
- Pydantic v1: Uses `BaseSettings` from `pydantic`
- Pydantic v2: Uses `BaseSettings` from `pydantic_settings`

### Sync vs Async

The Amadeus client uses synchronous `httpx.Client` for simplicity and reliability. The FastAPI routes use `run_in_threadpool` to avoid blocking the event loop when calling the sync client.

## Common IATA Codes

For testing and reference, here are some common airport codes:

| Code | City | Country |
|------|------|---------|
| BLR | Bangalore | India |
| DEL | Delhi | India |
| BOM | Mumbai | India |
| DXB | Dubai | UAE |
| SIN | Singapore | Singapore |
| LON | London | UK |
| NYC | New York | USA |
| LAX | Los Angeles | USA |

## Troubleshooting

### Token Acquisition Fails
- Verify your `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` are correct
- Check that you're using the correct `AMADEUS_BASE_URL` (test vs production)
- Run `python tools/test_amadeus_token.py` for detailed diagnostics

### No Results Returned
- Verify IATA codes are correct (3-letter codes)
- Ensure departure date is in the future
- Check that the route exists for the selected dates
- Some routes may have limited availability

### Rate Limiting
- The application automatically handles 429 responses
- Consider implementing request throttling on the client side
- Production environments should use proper rate limiting middleware

## Contributing

When contributing to this project:
1. Follow existing code style and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure environment variables are not committed

## Security Notes

- Never commit `.env` file or real credentials to version control
- Use environment variables for all sensitive configuration
- Rotate API credentials regularly
- Use HTTPS in production
- Implement proper authentication for production deployments

## License

[Add your license information here]

## Support

For issues and questions:
- Check existing documentation
- Review API logs for error details
- Test with diagnostic tools in `tools/` directory
- Consult [Amadeus API Documentation](https://developers.amadeus.com/self-service)
