# Development Guide

This guide provides information for developers who want to contribute to or extend the FareAround backend.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- A text editor or IDE (VS Code, PyCharm, etc.)
- Amadeus API credentials (get them at [developers.amadeus.com](https://developers.amadeus.com/))

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd farearound-backend
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Amadeus credentials
   ```

5. **Verify installation**:
   ```bash
   python tools/test_amadeus_token.py
   ```

### Running in Development Mode

Start the development server with auto-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables hot reloading, so the server will automatically restart when you make code changes.

Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Architecture

### Directory Structure

```
farearound-backend/
├── app/                      # Main application package
│   ├── api/                  # API layer
│   │   ├── amadeus_client.py # Amadeus API client
│   │   └── routes.py         # API route handlers
│   ├── core/                 # Core functionality
│   │   └── config.py         # Configuration management
│   └── main.py               # FastAPI application setup
├── tools/                    # Development and testing tools
│   ├── test_amadeus_token.py
│   └── test_search_flights.py
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
├── API.md                    # API documentation
└── DEVELOPMENT.md            # This file
```

### Key Design Patterns

#### 1. Dependency Injection

FastAPI's dependency injection is used for configuration:

```python
from fastapi import Depends
from ..core.config import get_settings

@router.get("/example")
def example_endpoint(settings=Depends(get_settings)):
    # Use settings.amadeus_client_id, etc.
    pass
```

#### 2. Async/Await Pattern

Routes use async handlers for better concurrency:

```python
@router.get("/search/flights")
async def get_flights(...):
    # Async operation
    raw = await run_in_threadpool(search_flights, params)
    return process_results(raw)
```

#### 3. TTL Caching

Custom TTL cache implementation for API responses:

```python
_response_cache = TTLCache(ttl=60, maxsize=512)

def search_flights(params):
    key = _make_cache_key(endpoint, params)
    cached = _response_cache.get(key)
    if cached:
        return cached
    
    data = _request_with_retries("GET", endpoint, params)
    _response_cache.set(key, data)
    return data
```

#### 4. Retry Pattern

Exponential backoff for transient failures:

```python
def _request_with_retries(method, url, params, max_attempts=4):
    backoff = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            # Make request
            return response.json()
        except Exception:
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 2
            else:
                raise
```

## Code Style and Standards

### Python Style Guide

Follow PEP 8 style guidelines:
- Use 4 spaces for indentation
- Maximum line length: 120 characters
- Use snake_case for functions and variables
- Use PascalCase for classes
- Add docstrings to functions and classes

### Type Hints

Use type hints for better code clarity and IDE support:

```python
from typing import Dict, List, Any, Optional

def process_offers(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    offers = raw.get("data", [])
    # Process offers
    return simplified
```

### Documentation

- Add docstrings to all public functions and classes
- Use inline comments for complex logic
- Keep README.md and API.md up to date
- Document environment variables in .env.example

### Example Function Documentation

```python
def search_flights(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for flight offers using Amadeus API.
    
    Args:
        params: Dictionary containing search parameters:
            - originLocationCode: IATA code for origin
            - destinationLocationCode: IATA code for destination
            - departureDate: Date in YYYY-MM-DD format
            - adults: Number of adult passengers
            - nonStop: Boolean for non-stop filter
            - max: Maximum number of results
    
    Returns:
        Dictionary containing Amadeus API response
    
    Raises:
        httpx.HTTPStatusError: If API request fails
        RuntimeError: If all retry attempts are exhausted
    """
    # Implementation
```

## Testing

### Manual Testing Tools

#### Test Token Acquisition

```bash
python tools/test_amadeus_token.py
```

This verifies:
- Credentials are configured correctly
- Network connectivity to Amadeus API
- Token endpoint is accessible

#### Test Flight Search

```bash
python tools/test_search_flights.py
```

This performs an end-to-end test:
- Token acquisition
- Flight search API call
- Response normalization
- Data transformation

### Interactive Testing

Use the Swagger UI at http://localhost:8000/docs:
1. Navigate to the endpoint you want to test
2. Click "Try it out"
3. Enter parameters
4. Click "Execute"
5. Review the response

### Testing with cURL

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test flight search
curl "http://localhost:8000/api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=1"
```

## Adding New Features

### Adding a New API Endpoint

1. **Define the route in `app/api/routes.py`**:

```python
@router.get("/search/new-feature")
async def new_feature(
    param1: str = Query(..., description="Parameter description"),
    param2: int = Query(1, ge=1, le=10),
):
    try:
        # Implement logic
        result = await process_request(param1, param2)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
```

2. **Update API documentation** in `API.md`

3. **Test the endpoint** using Swagger UI or cURL

4. **Update README.md** if needed

### Adding a New Amadeus API Integration

1. **Add function to `app/api/amadeus_client.py`**:

```python
def search_new_resource(params: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = f"{AMADEUS_API_BASE}/v1/resource/endpoint"
    key = _make_cache_key(endpoint, params)
    cached = _response_cache.get(key)
    if cached is not None:
        logger.debug("Returning cached result for key=%s", key)
        return cached
    
    data = _request_with_retries("GET", endpoint, params=params)
    _response_cache.set(key, data)
    return data
```

2. **Add route handler** in `app/api/routes.py`

3. **Test the integration**

### Adding Configuration Options

1. **Update `app/core/config.py`**:

```python
class Settings(BaseSettings):
    # Existing fields...
    new_config_option: str = "default_value"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

2. **Update `.env.example`**:

```env
NEW_CONFIG_OPTION=example_value
```

3. **Document in README.md** under Configuration section

## Common Development Tasks

### Viewing Logs

The application uses Python's built-in logging. To see logs:

```bash
# Run with uvicorn (logs go to stdout)
uvicorn app.main:app --reload --log-level debug
```

### Debugging

Add breakpoints or print statements:

```python
import logging
logger = logging.getLogger("farearound.debug")

@router.get("/endpoint")
async def endpoint():
    logger.debug("Debug message: %s", some_variable)
    # Your code
```

### Clearing Cache

The in-memory cache is cleared on server restart. During development with `--reload`, the cache is cleared on each code change.

### Testing Different Amadeus Environments

Switch between test and production:

```env
# Test environment (default)
AMADEUS_BASE_URL=https://test.api.amadeus.com

# Production environment
AMADEUS_BASE_URL=https://api.amadeus.com
```

**Warning**: Production API has rate limits and may incur costs.

## Troubleshooting

### Import Errors

If you get import errors:
1. Ensure virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Verify you're running from the correct directory

### Token Acquisition Fails

1. Check credentials in `.env`
2. Verify network connectivity
3. Run diagnostic: `python tools/test_amadeus_token.py`
4. Check Amadeus API status at [status.amadeus.com](https://status.amadeus.com/)

### No Results from API

1. Verify IATA codes are correct
2. Check date is in the future
3. Review Amadeus logs for errors
4. Test with known working parameters (e.g., BLR to DXB)

### Cache Issues

If seeing stale data:
1. Restart the server to clear cache
2. Adjust TTL in `amadeus_client.py` if needed
3. Disable cache temporarily for debugging

## Performance Considerations

### Caching Strategy

- **Token Cache**: Prevents redundant OAuth2 token requests
- **Response Cache**: 60-second TTL reduces duplicate API calls
- **Cache Size**: 512 entries (adjust based on traffic)

### Concurrency

- FastAPI runs async by default
- Sync Amadeus client runs in threadpool
- Consider connection pooling for high traffic

### Rate Limiting

Amadeus API has rate limits:
- Test environment: More lenient
- Production: Stricter limits
- Implement client-side rate limiting for high-traffic scenarios

## Security Best Practices

### Credentials Management

- Never commit `.env` file
- Use environment variables for all secrets
- Rotate credentials regularly
- Use different credentials for dev/prod

### API Security

- Implement authentication in production
- Restrict CORS origins in production
- Use HTTPS in production
- Implement request rate limiting
- Validate all user inputs

### Logging

- Never log credentials or tokens
- Sanitize logs of sensitive data
- Use appropriate log levels
- Consider structured logging for production

## Deployment Considerations

### Production Checklist

- [ ] Set production Amadeus credentials
- [ ] Configure production `AMADEUS_BASE_URL`
- [ ] Restrict CORS to allowed origins
- [ ] Enable HTTPS
- [ ] Implement authentication
- [ ] Set up monitoring and alerting
- [ ] Configure proper logging
- [ ] Set up rate limiting
- [ ] Configure appropriate cache sizes
- [ ] Use process manager (e.g., systemd, supervisor)

### Running in Production

Use a production ASGI server with multiple workers:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables in Production

Set environment variables through your deployment platform:
- Heroku: Use Config Vars
- AWS: Use Systems Manager Parameter Store
- Docker: Use environment files or secrets
- Kubernetes: Use ConfigMaps and Secrets

## Contributing

When contributing:
1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Update documentation
5. Submit a pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Amadeus for Developers](https://developers.amadeus.com/)
- [Amadeus API Reference](https://developers.amadeus.com/self-service)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HTTPX Documentation](https://www.python-httpx.org/)

## Getting Help

If you need help:
1. Check this guide and README.md
2. Review FastAPI and Amadeus documentation
3. Check application logs
4. Use diagnostic tools in `tools/` directory
5. Review Amadeus API status page
