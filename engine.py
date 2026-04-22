import os
import asyncio
import httpx
import google.generativeai as genai
import pickle
import joblib
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

class EnsembleEngine:
    def __init__(self, use_local_model: bool = False):
        self.sources = [
            {"name": "Wikipedia", "id": "wikipedia"},
            {"name": "HackerNews", "id": "hackernews"},
            {"name": "Reddit", "id": "reddit"},
            {"name": "Crossref", "id": "crossref"}
        ]
        
        # Initialize toggle and local model
        self.use_local_model = use_local_model
        self.local_model = None
        self.vectorizer = None
        self._load_local_models()

    def _load_local_models(self):
        """Load local model and vectorizer from pickle files."""
        try:
            if os.path.exists("model.pkl"):
                self.local_model = joblib.load("model.pkl")
                print("✓ Local model loaded successfully")
            else:
                print("⚠ model.pkl not found")
        except Exception as e:
            print(f"✗ Error loading model.pkl: {str(e)}")
        
        try:
            if os.path.exists("vectorizer.pkl"):
                self.vectorizer = joblib.load("vectorizer.pkl")
                print("✓ Vectorizer loaded successfully")
            else:
                print("⚠ vectorizer.pkl not found")
        except Exception as e:
            print(f"✗ Error loading vectorizer.pkl: {str(e)}")
    
    def classify_with_local_model(self, claim: str) -> Dict[str, Any]:
        """Classify claim using local pickle model - returns only True or False."""
        if not self.local_model or not self.vectorizer:
            return {
                "claim": claim,
                "verdict": "False",
                "explainability": "Local models not available",
                "sources": [],
                "engine": "Local Model",
                "confidence": 0
            }
        
        try:
            # Vectorize the claim
            claim_vector = self.vectorizer.transform([claim])
            
            # Predict
            prediction = self.local_model.predict(claim_vector)[0]
            confidence = max(self.local_model.predict_proba(claim_vector)[0]) * 100
            
            # Map prediction to True or False only
            verdict = "True" if prediction else "False"
            
            return {
                "claim": claim,
                "verdict": verdict,
                "explainability": f"Local model classification: {verdict} (confidence: {confidence:.1f}%)",
                "sources": [{"source": "Local Model", "status": verdict, "explanation": f"Confidence: {confidence:.1f}%", "confidence": int(confidence)}],
                "engine": "Local Model",
                "confidence": confidence
            }
        except Exception as e:
            print(f"LOCAL MODEL ERROR: {str(e)}")
            return {
                "claim": claim,
                "verdict": "False",
                "explainability": f"Local model error: {str(e)}",
                "sources": [],
                "engine": "Local Model",
                "confidence": 0
            }

    async def fetch_source_data(self, source_id: str, claim: str) -> str:
        """Fetch high-quality, rich search snippets from public APIs."""
        import urllib.parse
        safe_claim = urllib.parse.quote_plus(claim)
        
        # Wikipedia requires a descriptive User-Agent with contact info
        headers = {
            "User-Agent": "VeritasAI/1.0 (https://veritas.ai; contact: research@veritas.ai) Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                print(f"DEBUG: Fetching {source_id} for claim: {claim}")
                
                if source_id == "wikipedia":
                    # Step 1: Search for the title
                    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_claim}&format=json"
                    search_resp = await client.get(search_url)
                    if search_resp.status_code != 200: return f"Wikipedia Search Error: {search_resp.status_code}"
                    search_data = search_resp.json()
                    search_results = search_data.get("query", {}).get("search", [])
                    if not search_results: return f"Wikipedia Result: No relevant pages found for '{claim}'."
                    
                    # Step 2: Extract text from the top result
                    top_page = search_results[0].get("title", "")
                    extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={urllib.parse.quote(top_page)}&format=json"
                    extract_resp = await client.get(extract_url)
                    if extract_resp.status_code != 200: return f"Wikipedia Extract Error: {extract_resp.status_code}"
                    extract_data = extract_resp.json()
                    pages = extract_data.get("query", {}).get("pages", {})
                    for page_id in pages:
                        content = pages[page_id].get("extract", "No extract available.")[:800]
                        print(f"DEBUG: Wikipedia fetched {len(content)} chars.")
                        return content
                    return "Wikipedia Result: No extract content found."

                elif source_id == "hackernews":
                    # Algolia search
                    url = f"https://hn.algolia.com/api/v1/search?query={safe_claim}&tags=story"
                    resp = await client.get(url)
                    data = resp.json()
                    hits = data.get("hits", [])
                    if not hits: return "HackerNews Result: No relevant tech discussions found."
                    content = "\n\n".join([f"THREAT: {h.get('title', '')}\nCONTENT: {h.get('story_text', '')[:300]}" for h in hits[:2]])
                    print(f"DEBUG: HackerNews fetched {len(content)} chars.")
                    return content
                
                elif source_id == "reddit":
                    # Reddit public search
                    url = f"https://www.reddit.com/search.json?q={safe_claim}&limit=5&sort=relevance"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        if not posts: return "Reddit Result: No community discussions found."
                        snippets = []
                        for p in posts:
                            d = p['data']
                            snippets.append(f"POST: {d.get('title')} (Subreddit: {d.get('subreddit')})\nTEXT: {d.get('selftext', '')[:400]}")
                        content = "\n\n".join(snippets)
                        print(f"DEBUG: Reddit fetched {len(content)} chars.")
                        return content
                    return f"Reddit API Error ({resp.status_code})"
                
                elif source_id == "crossref":
                    # Scholarly papers
                    url = f"https://api.crossref.org/works?query={safe_claim}&rows=5"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("message", {}).get("items", [])
                        if not items: return "Crossref Result: No scholarly publications found."
                        snippets = []
                        for i in items:
                            title = i.get('title', ['Untitled'])[0]
                            abstract = i.get('abstract', 'No abstract available')
                            snippets.append(f"PAPER: {title}\nABSTRACT: {abstract[:400]}")
                        content = "\n\n".join(snippets)
                        print(f"DEBUG: Crossref fetched {len(content)} chars.")
                        return content
                    return f"Crossref API Error ({resp.status_code})"
                
                else:
                    return f"Source '{source_id}' is not yet supported."
        except Exception as e:
            print(f"ERROR Fetching {source_id}: {str(e)}")
            return f"{source_id} Error: {str(e)}"

    async def analyze_claim(self, claim: str, use_local: bool = None) -> Dict[str, Any]:
        """
        Analyze claim using either API or local model.
        
        Args:
            claim: The claim to analyze
            use_local: Override the default toggle (None = use self.use_local_model)
        """
        # Determine which method to use
        prefer_local = use_local if use_local is not None else self.use_local_model
        print(f"[ENGINE] use_local param: {use_local} | self.use_local_model: {self.use_local_model} | prefer_local: {prefer_local}")
        
        # If local model is preferred
        if prefer_local:
            print(f"[ENGINE] ✓ Using LOCAL model (model.pkl only)")
            return self.classify_with_local_model(claim)
        
        # Otherwise try API first, with fallback to local model
        print(f"[ENGINE] ✓ Using API (Gemini) first")
        try:
            # Step 1: Fetch snippets for all sources concurrently
            fetch_tasks = [self.fetch_source_data(s["id"], claim) for s in self.sources]
            snippets = await asyncio.gather(*fetch_tasks)

            # Step 2: Single aggregate call to Gemini
            aggregated_snippets = ""
            for i, s in enumerate(self.sources):
                aggregated_snippets += f"--- Source: {s['name']} ---\n{snippets[i]}\n\n"

            prompt = f"""
            Analyze the following claim based on the provided source snippets.
            
            Claim: "{claim}"
            
            Sources Content:
            {aggregated_snippets}
            
            Instructions:
            1. For each source, explicitly determine if it supports (TRUE), refutes (FALSE), or doesn't have info (UNVERIFIED).
            2. If a source says 'Error' or 'No results', it is UNVERIFIED.
            3. Provide a short explanation and confidence score for each.
            4. Determine the final verdict based on this logic:
               - "Real": 2+ sources say TRUE
               - "Likely Real": 1 source says TRUE
               - "Fake": 2+ sources say FALSE
               - "Likely Fake": 1 source says FALSE
               - "Unverified": 0 sources provide definitive info
            5. Provide an overall consensus explanation.
            
            Return exactly as JSON:
            {{
                "verdict": "Real | Likely Real | Fake | Likely Fake | Unverified",
                "explainability": "...",
                "sources": [
                    {{
                        "source": "Wikipedia",
                        "status": "TRUE | FALSE | UNVERIFIED",
                        "explanation": "...",
                        "confidence": 85
                    }},
                    ...
                ]
            }}
            """
            
            response = await model.generate_content_async(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            import json
            result = json.loads(response.text)
            result["claim"] = claim
            result["engine"] = "Gemini 2.5 Flash"
            return result
            
        except Exception as e:
            print(f"API ERROR: {str(e)}")
            print(f"DEBUG: Falling back to local model")
            # Fallback to local model
            return self.classify_with_local_model(claim)
