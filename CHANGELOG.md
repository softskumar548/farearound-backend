# Changelog

All notable changes to the FareAround Backend project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Comprehensive project documentation (README.md, API.md, DEVELOPMENT.md)
- This CHANGELOG file to track project changes

## [0.1.0] - 2026-02-11

### Added

#### Core Features
- FastAPI-based REST API server
- Integration with Amadeus Travel API
- Flight search endpoint (`/api/search/flights`)
- Hotel search endpoint (`/api/search/hotels`)
- Affiliate information endpoint (`/api/affiliate/info`)
- Health check endpoint (`/health`)

#### Amadeus Integration
- Custom Amadeus API client (`app/api/amadeus_client.py`)
- OAuth2 client credentials authentication with automatic token management
- Token caching with configurable expiry
- Response caching with 60-second TTL
- Thread-safe TTL cache implementation (512 items max)
- Retry logic with exponential backoff for transient failures
- Rate limiting support (handles 429 responses and Retry-After headers)
- Network error handling and automatic retries

#### Configuration
- Environment-based configuration using Pydantic
- Support for both Pydantic v1 and v2
- Configuration for Amadeus API credentials
- Configurable base URL for test/production environments
- Support for affiliate tracking configuration

#### API Features
- CORS middleware for cross-origin requests
- Comprehensive query parameter validation
- Flight search with:
  - Origin and destination IATA codes
  - Departure date
  - Number of adults (1-9)
  - Non-stop flight filtering
  - Configurable result limits (1-50)
  - Currency selection (default: INR)
- Response normalization for flight offers
- Simplified response format with:
  - Price information
  - Flight segments
  - Duration details
  - Carrier and flight number
  
#### Testing Tools
- Token acquisition diagnostic script (`tools/test_amadeus_token.py`)
- End-to-end flight search test script (`tools/test_search_flights.py`)

#### Documentation
- Example environment configuration (`.env.example`)
- Python dependencies specification (`requirements.txt`)

#### Development Infrastructure
- Git repository initialization
- `.gitignore` for Python projects

### Technical Details

#### Dependencies
- FastAPI >= 0.95.0 - Web framework
- Uvicorn >= 0.22.0 - ASGI server
- Pydantic >= 1.10.0 - Data validation
- HTTPX >= 0.24.0 - HTTP client
- python-dotenv >= 1.0.0 - Environment variable management
- Amadeus >= 4.0.0 - Optional official SDK

#### Architecture Highlights
- Lightweight custom Amadeus client (no heavy SDK dependencies)
- Thread-safe token and response caching
- Async FastAPI routes with sync client in threadpool
- Configurable retry logic and backoff strategy
- LRU-like cache eviction policy

#### Performance Features
- In-memory TTL caching reduces API calls
- Token reuse prevents redundant OAuth2 requests
- Automatic retry prevents transient failure errors
- Concurrent request support with thread safety

### Implementation Notes

The initial implementation focused on:
1. **Reliability**: Robust error handling, retries, and rate limit management
2. **Performance**: Intelligent caching to reduce API calls and improve response times
3. **Simplicity**: Minimal dependencies, clean architecture, easy to understand and extend
4. **Flexibility**: Environment-based configuration, support for test and production APIs

### Known Limitations

- No authentication/authorization for API endpoints (designed for internal use or to be deployed behind a gateway)
- Hotel search returns raw Amadeus response (not normalized like flights)
- In-memory cache (not distributed, resets on server restart)
- No persistent storage or database
- No booking functionality (search only)
- No support for round-trip or multi-city flights yet
- CORS configured for all origins (should be restricted in production)

### Future Considerations

Potential enhancements for future versions:
- User authentication and authorization
- Persistent caching (Redis, Memcached)
- Round-trip flight search
- Multi-city itineraries
- Flight booking endpoints
- Hotel booking endpoints
- Database integration for storing searches and bookings
- User preferences and saved searches
- Email notifications
- Payment integration
- Admin dashboard
- Analytics and reporting
- Rate limiting middleware
- Request/response logging
- Metrics and monitoring
- API versioning
- GraphQL API option
- WebSocket support for real-time updates

### Credits

Initial implementation by cvak48-ai on February 11, 2026.

---

## Version History

- **0.1.0** (2026-02-11) - Initial release with core flight/hotel search functionality
- **Unreleased** - Documentation additions

[Unreleased]: https://github.com/softskumar548/farearound-backend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/softskumar548/farearound-backend/releases/tag/v0.1.0
