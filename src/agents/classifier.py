import os
from typing import Dict, Any

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def _llm_classify(text: str) -> Dict[str, Any]:
    """Try to use LangChain + OpenAI to classify. Returns dict with keys: category, sentiment, confidence."""
    try:
        # Lazy imports so the module can still be used without langchain installed.
        from langchain import LLMChain, PromptTemplate
        from langchain.llms import OpenAI

        # Stronger prompt with explicit schema and examples.
        prompt = PromptTemplate(
            input_variables=["text"],
            template=(
                "You are an assistant that classifies parent feedback for a university.\n"
                "Output must be valid JSON and nothing else. The JSON must contain the keys:\n"
                "  - category: one of [Academics, Administration, Housing, Finance, Facilities, Other]\n"
                "  - sentiment: one of [positive, neutral, negative]\n"
                "  - confidence: a number between 0 and 1 representing your confidence in the classification\n\n"
                "Example output:\n"
                "{\n  \"category\": \"Facilities\",\n  \"sentiment\": \"negative\",\n  \"confidence\": 0.86\n}\n\n"
                "Now analyze the following feedback and respond ONLY with the JSON object (no explanation):\n\n"
                "Feedback: {text}\n"
            ),
        )

        llm = OpenAI(openai_api_key=OPENAI_KEY, temperature=0)
        chain = LLMChain(llm=llm, prompt=prompt)
        out = chain.run(text=text)
        # The LLM is asked to return JSON; try to parse (allow for surrounding whitespace/newlines)
        import json, re

        def _extract_json(s: str) -> str:
            # Find first { and last } to extract a JSON substring
            start = s.find("{")
            end = s.rfind("}")
            if start == -1 or end == -1 or end <= start:
                # fallback to regex
                m = re.search(r"(\{.*\})", s, re.S)
                if m:
                    return m.group(1)
                raise ValueError("No JSON object found in LLM output")
            return s[start : end + 1]

        raw = out.strip()
        js = _extract_json(raw)
        parsed = json.loads(js)

        # Basic validation and normalization
        allowed = {"Academics", "Administration", "Housing", "Finance", "Facilities", "Other"}
        category = parsed.get("category")
        if category not in allowed:
            category = "Other"

        sentiment = parsed.get("sentiment", "neutral")
        if sentiment not in {"positive", "neutral", "negative"}:
            sentiment = "neutral"

        try:
            confidence = float(parsed.get("confidence", 0.5))
        except Exception:
            confidence = 0.5
        # Clamp
        confidence = max(0.0, min(1.0, confidence))

        return {"category": category, "sentiment": sentiment, "confidence": confidence}
    except Exception:
        # If anything fails, raise so fallback can be used
        raise


def _fallback_classify(text: str) -> Dict[str, Any]:
    # Lightweight keyword mapping and VADER sentiment
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except Exception:
        # If vader not installed, provide a very small fallback
        analyzer = None
    else:
        analyzer = SentimentIntensityAnalyzer()

    keywords = {
        "Academics": ["course", "exam", "professor", "grade", "curriculum", "homework", "lecture"],
        "Administration": ["admission", "admissions", "registration", "admin", "office", "policy", "staff"],
        "Housing": ["dorm", "housing", "room", "apartment", "accommodation", "residence"],
        "Finance": ["tuition", "fee", "fees", "payment", "scholarship", "refund"],
        "Facilities": ["parking", "food", "cafeteria", "library", "facility", "maintenance", "campus"],
    }

    text_l = text.lower()
    scores = {k: 0 for k in keywords.keys()}
    for cat, terms in keywords.items():
        for t in terms:
            if t in text_l:
                scores[cat] += 1

    # pick best category
    best_cat = "Other"
    best_score = 0
    if scores:
        best_cat, best_score = max(scores.items(), key=lambda x: x[1])
        if best_score == 0:
            best_cat = "Other"

    # sentiment
    sentiment = "neutral"
    confidence = 0.6
    if analyzer:
        vs = analyzer.polarity_scores(text)
        c = vs.get("compound", 0.0)
        if c >= 0.05:
            sentiment = "positive"
        elif c <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        # map compound magnitude into confidence
        confidence = min(0.95, 0.5 + abs(c))
    else:
        # crude rule-based sentiment
        if any(w in text_l for w in ["not happy", "angry", "bad", "poor", "unacceptable", "disappointed"]):
            sentiment = "negative"
            confidence = 0.7
        elif any(w in text_l for w in ["great", "happy", "satisfied", "excellent", "thank"]):
            sentiment = "positive"
            confidence = 0.7

    return {"category": best_cat, "sentiment": sentiment, "confidence": float(confidence)}


def analyze_feedback(text: str) -> Dict[str, Any]:
    """Public API: analyze the feedback text and return a dict.

    It will try to use the LLM-backed LangChain agent if OPENAI_API_KEY is present and the libs are installed.
    Otherwise, it runs a local fallback.
    """
    if OPENAI_KEY:
        try:
            return _llm_classify(text)
        except Exception:
            # fallback on any failure
            return _fallback_classify(text)
    else:
        return _fallback_classify(text)
