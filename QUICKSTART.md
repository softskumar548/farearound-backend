# Quick Start Guide

Get the FareAround backend up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Amadeus API credentials ([Get them here](https://developers.amadeus.com/))

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd farearound-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your Amadeus credentials

# 4. Run the server
uvicorn app.main:app --reload --port 8000
```

## Test It

```bash
# Open in browser
http://localhost:8000/docs

# Or use curl
curl "http://localhost:8000/api/search/flights?origin=BLR&destination=DXB&departureDate=2026-04-30&adults=1"
```

## What's Next?

- 📖 Read the [full README](README.md) for detailed information
- 🔌 Check out the [API documentation](API.md) for all endpoints
- 💻 See the [Development Guide](DEVELOPMENT.md) for contributing
- 📝 Review the [Changelog](CHANGELOG.md) for version history

## Common Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Test Amadeus token
python tools/test_amadeus_token.py

# Test flight search
python tools/test_search_flights.py
```

## Need Help?

1. Check the [README.md](README.md) troubleshooting section
2. Review your `.env` configuration
3. Verify your Amadeus credentials
4. Check the application logs

## Documentation Overview

| File | Purpose |
|------|---------|
| [README.md](README.md) | Main project documentation |
| [API.md](API.md) | Detailed API endpoint reference |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developer guide and best practices |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |
| [QUICKSTART.md](QUICKSTART.md) | This quick start guide |

Happy coding! 🚀
