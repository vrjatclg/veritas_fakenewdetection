# VeritasAI - Ensemble Fact Intelligence

An advanced fact-checking and claim verification application that uses an ensemble approach with multiple information sources and AI models to determine the veracity of claims and statements.

## 🎯 Overview

VeritasAI analyzes claims by synthesizing information from multiple sources (Wikipedia, HackerNews, Reddit, and Crossref) and leveraging AI models to provide a consensus verdict with detailed explainability. The system supports both cloud-based (Gemini API) and local machine learning models.

## ✨ Features

- **Ensemble Analysis**: Queries multiple data sources simultaneously for comprehensive fact-checking
- **Dual Engine Support**: 
  - Google Gemini API for advanced AI-powered analysis
  - Local machine learning model for offline processing
  - Automatic fallback mechanism if primary engine fails
- **Consensus Verdict**: Aggregates results from multiple sources to provide a single, reliable verdict
- **Explainability**: Provides detailed reasoning for the verdict
- **Interactive UI**: Modern, dark-themed web interface with real-time progress tracking
- **Source Transparency**: Shows which sources were queried and their individual verdicts

## 📋 Project Structure

```
ml_model_startagain/
├── main.py              # FastAPI application server
├── engine.py            # Core ensemble analysis engine
├── model.pkl            # Trained ML model (optional)
├── vectorizer.pkl       # Text vectorizer for local model (optional)
├── templates/
│   └── index.html       # Main UI template
├── static/
│   ├── app.js          # Frontend logic and interactions
│   └── style.css       # UI styling
└── .env                # Environment configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip/pipenv
- Google Gemini API key (for API-based analysis)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd ml_model_startagain
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn pydantic google-generativeai httpx python-dotenv joblib
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the server**
   ```bash
   python main.py
   ```

6. **Access the application**
   Open your browser and navigate to:
   ```
   http://localhost:8001
   ```

## 📖 Usage

### Analyzing a Claim

1. Enter a claim or statement in the input field
2. Click "Analyse Claim" to start the verification process
3. Watch the real-time progress as the engine queries sources
4. View the consensus verdict and detailed analysis in the results section
5. Click "New Analysis" to verify another claim

### API Endpoints

#### GET `/`
Returns the main web interface (HTML)

#### POST `/analyze`
Analyzes a claim and returns verdict with explainability
- **Request body**:
  ```json
  {
    "claim": "Your claim to verify",
    "use_local": false
  }
  ```
- **Response**:
  ```json
  {
    "claim": "Your claim",
    "verdict": "True/False",
    "explainability": "Detailed reasoning",
    "sources": [...],
    "engine": "Gemini Flash/Local Model",
    "confidence": 85.5
  }
  ```

#### GET `/config`
Retrieves current engine configuration
- Returns: Active mode (API/Local), model availability, fallback settings

#### POST `/config/toggle`
Switches between API and local model
- **Query parameter**: `use_local=true/false`
- **Response**: Confirmation of mode switch

## 🔧 Configuration

The application supports two analysis modes:

### API Mode (Default)
- Uses Google Gemini 2.5 Flash model
- Requires valid API key
- Provides advanced reasoning and analysis
- Best for complex claims

### Local Model Mode
- Uses trained pickle model and vectorizer
- No API key required
- Faster offline processing
- Requires `model.pkl` and `vectorizer.pkl` files

**Auto-fallback**: If API fails, system automatically falls back to local model

## 📊 Information Sources

The ensemble queries the following sources for fact-checking:

1. **Wikipedia**: Factual encyclopedia data
2. **HackerNews**: Technology and current events
3. **Reddit**: Community discussions and insights
4. **Crossref**: Academic and scientific publications

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS)
        ↓
    FastAPI Server
        ↓
  Ensemble Engine
        ├─→ Source Fetcher (Wikipedia, HN, Reddit, Crossref)
        ├─→ Local Model (Optional)
        └─→ Gemini API (Primary)
        ↓
    Analysis Results
```

## 🔐 Security Considerations

- API keys are stored in `.env` files (not committed to version control)
- HTTP requests use proper User-Agent headers
- Input validation through Pydantic models
- CORS can be configured as needed

## 🛠️ Development

### Adding a New Source

Edit `engine.py` and add to the `sources` list in `EnsembleEngine.__init__()`:

```python
self.sources = [
    # ... existing sources ...
    {"name": "NewSource", "id": "newsource"}
]
```

Then implement the fetch logic in `fetch_source_data()`.

### Customizing Analysis Logic

Modify the `analyze_claim()` method in `engine.py` to adjust:
- How verdicts are aggregated
- Confidence thresholds
- Explainability generation

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes (for API mode) |

## 🐛 Troubleshooting

**Issue**: "model.pkl not found"
- **Solution**: This is optional. Ensure you have the pickle files if using local model mode

**Issue**: API key errors
- **Solution**: Verify `GEMINI_API_KEY` is set correctly in `.env`

**Issue**: Port 8001 already in use
- **Solution**: Modify the port in `main.py` or kill the process using that port

## 📦 Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **google-generativeai**: Gemini API client
- **httpx**: Async HTTP requests
- **joblib**: Model serialization
- **python-dotenv**: Environment configuration

## 🎨 UI Features

- **Dark Theme**: Eye-friendly interface designed for extended use
- **Real-time Progress**: Visual feedback during analysis
- **Source Transparency**: Individual source verdicts displayed
- **Responsive Design**: Works on desktop and tablet devices
- **Lucide Icons**: Clean, modern iconography

## 📄 License

[Add your license information here]

## 👤 Author

Created by Viraj

## 🙋 Support

For issues, questions, or suggestions, please refer to the project documentation or contact the development team.
