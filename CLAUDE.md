# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PSI API - A FastAPI-based service that detects client profiles for real estate chatbots in 0.3 seconds. The API uses pattern matching and keyword analysis to identify client types (investor, family, speculator, foreigner, first-time buyer) and returns personalized approach suggestions.

**Live Production URL:** https://psi-api-ve66.onrender.com
**GitHub Repository:** https://github.com/bitcoinmunist/psi-api

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run API locally
python run_api.py
# Or directly:
python psi_api_final.py

# Access endpoints:
# http://localhost:8000/test - Visual test interface
# http://localhost:8000/docs - FastAPI documentation
# http://localhost:8000/health - Health check
```

### Testing the API
```bash
# Test with curl
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TRIAL_PSI_7DIAS" \
  -d '{"text": "Qual o ROI desse lançamento?"}'

# Production test
curl -X POST https://psi-api-ve66.onrender.com/detect \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TRIAL_PSI_7DIAS" \
  -d '{"text": "Qual o ROI esperado?"}'
```

### Deployment Commands
```bash
# Commit changes
git add .
git commit -m "Your message"

# Push to GitHub (requires token)
GIT_ASKPASS=echo git push https://ghp_[TOKEN]@github.com/bitcoinmunist/psi-api.git master:main

# Render will auto-deploy from GitHub pushes
```

## Architecture

### Core Components

**psi_api_final.py** - Main API implementation
- Profile detection engine using regex patterns
- Credit management system (Redis or local storage fallback)
- 5 client profiles with specific patterns and approaches
- Webhook support for async callbacks

**run_api.py** - Server startup script
- Configures trial API key (TRIAL_PSI_7DIAS)
- Sets up Uvicorn server with PORT from environment

**Key Design Decisions:**
- **No external AI dependencies** - Uses deterministic pattern matching for speed and cost efficiency
- **Redis optional** - Falls back to in-memory storage for development
- **Credit-based monetization** - Pre-paid credits model (Trial: 100, Starter: R$197/2000, Pro: R$497/6000)
- **Profile-specific responses** - Each profile has tailored approach and example responses

### API Request Flow
1. Request hits `/detect` endpoint with text and API key
2. API validates key and checks credits
3. Text analyzed against profile patterns (INVESTIDOR_EARLY_BIRD, FAMILIA_PLANEJADORA, etc.)
4. Returns profile, confidence, keywords, and suggested approach
5. Optional webhook callback for async processing

### Profile Detection Logic
- Profiles defined in `PROFILES_LANCAMENTO` dictionary
- Each profile has regex patterns, approach text, and example response
- Confidence calculated by (keywords_found * 0.15) capped at 0.9
- Default to PRIMEIRA_COMPRA if no patterns match

## Important Context

### Authentication
- Header-based auth: `X-API-Key`
- Trial key hardcoded: `TRIAL_PSI_7DIAS` (100 credits)
- Production keys managed via `add_credits()` function

### Deployment on Render
- Uses `render.yaml` for configuration
- Python 3.11 runtime
- Start command: `python run_api.py`
- Auto-deploys from GitHub main branch

### Current Status
- API live at https://psi-api-ve66.onrender.com
- Redis not configured (using local storage)
- Trial API key active with 100 credits

### Files Not to Commit
- `.env` files (use `.env.example` as template)
- Any files with API keys or tokens
- Local test data or logs

## Common Tasks

### Adding New Profile
1. Add to `PROFILES_LANCAMENTO` in psi_api_final.py
2. Include patterns, approach, and example fields
3. Test detection with relevant keywords

### Modifying Credit System
- Functions: `get_credits()`, `use_credit()`, `add_credits()`
- Redis keys format: `key:{api_key}`
- Local storage fallback in `LOCAL_STORAGE` dict

### Debugging Production
- Check `/health` endpoint for system status
- Verify credits with `/stats?key={API_KEY}`
- Monitor Render logs for deployment issues