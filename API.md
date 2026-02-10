# API Documentation

This document provides detailed information about all available API endpoints in the FareAround backend.

## Base URL

```
http://localhost:8000  (development)
https://your-domain.com  (production)
```

## Authentication

Currently, the API does not require authentication for client requests. The backend handles Amadeus API authentication internally using OAuth2 client credentials flow.

## Endpoints

### Health Check

#### `GET /health`

Simple health check endpoint to verify the service is running.

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response**:
- Status: `200 OK`
- Content-Type: `application/json`

```json
{
  "status": "ok"
}
```

---

### Flight Search

#### `GET /api/search/flights`

Search for flight offers between two locations.

**Request**:
```http
GET /api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=1&nonStop=false&max=20 HTTP/1.1
Host: localhost:8000
```

**Query Parameters**:

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `origin` | string | Yes | 3 characters, uppercase IATA code | Origin airport code (e.g., "BLR" for Bangalore) |
| `destination` | string | Yes | 3 characters, uppercase IATA code | Destination airport code (e.g., "DXB" for Dubai) |
| `departureDate` | string | Yes | Format: YYYY-MM-DD | Departure date |
| `adults` | integer | No | 1-9, default: 1 | Number of adult passengers |
| `nonStop` | boolean | No | default: false | Filter for non-stop flights only |
| `max` | integer | No | 1-50, default: 20 | Maximum number of results to return |

**Response**:
- Status: `200 OK`
- Content-Type: `application/json`

```json
{
  "query": {
    "origin": "BLR",
    "destination": "DXB",
    "departureDate": "2026-04-30",
    "adults": 1,
    "nonStop": false
  },
  "count": 2,
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
    },
    {
      "id": "2",
      "total": "28500.00",
      "currency": "INR",
      "duration": "PT6H15M",
      "segments": [
        {
          "from": "BLR",
          "to": "DOH",
          "departAt": "2026-04-30T08:00:00",
          "arriveAt": "2026-04-30T10:45:00",
          "carrier": "QR",
          "flightNumber": "512",
          "segmentDuration": "PT4H45M"
        },
        {
          "from": "DOH",
          "to": "DXB",
          "departAt": "2026-04-30T12:30:00",
          "arriveAt": "2026-04-30T14:15:00",
          "carrier": "QR",
          "flightNumber": "1024",
          "segmentDuration": "PT1H45M"
        }
      ]
    }
  ]
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `query` | object | Echo of the search parameters |
| `query.origin` | string | Origin airport code |
| `query.destination` | string | Destination airport code |
| `query.departureDate` | string | Departure date |
| `query.adults` | integer | Number of adult passengers |
| `query.nonStop` | boolean | Non-stop filter status |
| `count` | integer | Number of offers returned |
| `offers` | array | List of flight offers |
| `offers[].id` | string | Unique offer identifier |
| `offers[].total` | string | Total price |
| `offers[].currency` | string | Currency code (e.g., "INR", "USD") |
| `offers[].duration` | string | Total journey duration in ISO 8601 format |
| `offers[].segments` | array | List of flight segments |
| `offers[].segments[].from` | string | Departure airport IATA code |
| `offers[].segments[].to` | string | Arrival airport IATA code |
| `offers[].segments[].departAt` | string | Departure time (ISO 8601) |
| `offers[].segments[].arriveAt` | string | Arrival time (ISO 8601) |
| `offers[].segments[].carrier` | string | Airline carrier code |
| `offers[].segments[].flightNumber` | string | Flight number |
| `offers[].segments[].segmentDuration` | string | Segment duration in ISO 8601 format |

**Duration Format**:
The duration fields use ISO 8601 duration format:
- `PT4H30M` = 4 hours 30 minutes
- `PT1H45M` = 1 hour 45 minutes
- `PT45M` = 45 minutes

**Error Responses**:

1. Invalid IATA Code (422):
```json
{
  "detail": [
    {
      "loc": ["query", "origin"],
      "msg": "ensure this value has at most 3 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

2. Amadeus API Error (502):
```json
{
  "detail": "Amadeus API error message"
}
```

**Caching**:
- Responses are cached for 60 seconds
- Identical requests within the cache window return cached results
- Cache key includes all query parameters

---

### Hotel Search

#### `GET /api/search/hotels`

Search for hotel offers in a specific city.

**Request**:
```http
GET /api/search/hotels?cityCode=DEL&checkIn=2026-05-01&checkOut=2026-05-05 HTTP/1.1
Host: localhost:8000
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cityCode` | string | Yes | City IATA code (e.g., "DEL" for Delhi) |
| `checkIn` | string | Yes | Check-in date (YYYY-MM-DD format) |
| `checkOut` | string | Yes | Check-out date (YYYY-MM-DD format) |

**Response**:
- Status: `200 OK`
- Content-Type: `application/json`

Returns the raw Amadeus API response for hotel offers. See [Amadeus Hotel Search API](https://developers.amadeus.com/self-service/category/hotels/api-doc/hotel-search/api-reference) for response schema.

**Error Responses**:

1. Missing Parameters (422):
```json
{
  "detail": [
    {
      "loc": ["query", "cityCode"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

2. Amadeus API Error (502):
```json
{
  "detail": "Amadeus API error message"
}
```

**Caching**:
- Responses are cached for 60 seconds
- Identical requests within the cache window return cached results

---

### Affiliate Information

#### `GET /api/affiliate/info`

Retrieve configured affiliate information.

**Request**:
```http
GET /api/affiliate/info HTTP/1.1
Host: localhost:8000
```

**Response**:
- Status: `200 OK`
- Content-Type: `application/json`

```json
{
  "affiliate_id": "your_affiliate_id",
  "domain": "yourdomain.com"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `affiliate_id` | string \| null | Configured affiliate ID from environment |
| `domain` | string \| null | Configured domain from environment |

**Notes**:
- Returns `null` for fields not configured in environment variables
- Used for affiliate tracking and monetization

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 422 | Validation Error - Invalid request parameters |
| 502 | Bad Gateway - Upstream Amadeus API error |
| 500 | Internal Server Error |

## Rate Limiting

The backend automatically handles rate limiting from the Amadeus API:
- Respects `429 Too Many Requests` responses
- Honors `Retry-After` headers
- Implements exponential backoff
- Retries transient failures automatically

Clients should implement their own rate limiting to avoid overwhelming the backend.

## CORS

The API is configured to allow cross-origin requests from all origins (`*`). In production, this should be restricted to your frontend domains.

## Examples

### cURL Examples

**Flight Search**:
```bash
curl -X GET "http://localhost:8000/api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=2&nonStop=true&max=10"
```

**Hotel Search**:
```bash
curl -X GET "http://localhost:8000/api/search/hotels?cityCode=DEL&checkIn=2026-05-01&checkOut=2026-05-05"
```

**Health Check**:
```bash
curl -X GET "http://localhost:8000/health"
```

### JavaScript/Fetch Examples

**Flight Search**:
```javascript
const searchFlights = async () => {
  const params = new URLSearchParams({
    origin: 'BLR',
    destination: 'DXB',
    departureDate: '2026-04-30',
    adults: '1',
    nonStop: 'false',
    max: '20'
  });
  
  const response = await fetch(`http://localhost:8000/api/search/flights?${params}`);
  const data = await response.json();
  
  if (response.ok) {
    console.log(`Found ${data.count} flight offers`);
    data.offers.forEach(offer => {
      console.log(`Flight ${offer.id}: ${offer.currency} ${offer.total}`);
    });
  } else {
    console.error('Error:', data.detail);
  }
};
```

**Hotel Search**:
```javascript
const searchHotels = async () => {
  const params = new URLSearchParams({
    cityCode: 'DEL',
    checkIn: '2026-05-01',
    checkOut: '2026-05-05'
  });
  
  const response = await fetch(`http://localhost:8000/api/search/hotels?${params}`);
  const data = await response.json();
  
  if (response.ok) {
    console.log('Hotel offers:', data);
  } else {
    console.error('Error:', data.detail);
  }
};
```

### Python/Requests Examples

**Flight Search**:
```python
import requests

def search_flights():
    url = "http://localhost:8000/api/search/flights"
    params = {
        "origin": "BLR",
        "destination": "DXB",
        "departureDate": "2026-04-30",
        "adults": 1,
        "nonStop": False,
        "max": 20
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} flight offers")
        for offer in data['offers']:
            print(f"Flight {offer['id']}: {offer['currency']} {offer['total']}")
    else:
        print(f"Error: {response.json()['detail']}")
```

**Hotel Search**:
```python
import requests

def search_hotels():
    url = "http://localhost:8000/api/search/hotels"
    params = {
        "cityCode": "DEL",
        "checkIn": "2026-05-01",
        "checkOut": "2026-05-05"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("Hotel offers:", data)
    else:
        print(f"Error: {response.json()['detail']}")
```

## Testing

You can test the API interactively using the built-in Swagger UI:
- Navigate to `http://localhost:8000/docs`
- Click on an endpoint to expand it
- Click "Try it out"
- Fill in the parameters
- Click "Execute"

Alternative documentation format available at `http://localhost:8000/redoc`.

## Next Steps

- Implement authentication for production use
- Add more sophisticated error handling
- Implement request logging and monitoring
- Add support for round-trip flights
- Add support for multi-city itineraries
- Implement flight booking endpoints
- Add hotel booking endpoints
- Implement user preferences and saved searches
