"""Prompt templates and prompt builders for the travel planner workflow."""


FEATURE_EXTRACTION_SYSTEM_PROMPT = """
You are an ML feature extraction assistant.

Your job:
Extract ONLY structured ML input features from the user's trip request.
Do NOT predict the travel style label.
Do NOT recommend destinations.
Do NOT explain your reasoning.

Return ONLY valid JSON with exactly these keys:

{
  "avg cost (usd/day)": number,
  "avg_temp_year": number,
  "hiking_score": number,
  "beach_score": number,
  "nightlife_score": number,
  "culture_score": number,
  "food_score": number,
  "adventure_score": number,
  "nature_score": number,
  "safety_score": number,
  "accommodation_type": string,
  "terrain_type": string
}

Rules:
- Score fields must be numbers from 0 to 10.
- avg cost (usd/day) must be a realistic daily travel budget in USD.
- avg_temp_year must represent the user's preferred destination climate in Celsius.
- accommodation_type must be one of:
  ["Standard Hotel", "Resort/Apartment", "Guesthouse/Hostel"]
- terrain_type must be one of:
  ["Urban-Heritage", "Coastal", "Mountain-Nature"]
- If the user clearly mentions a preference, reflect it strongly.
- If the user does not mention a feature, infer a reasonable neutral value based on
  the destination semantics they describe.
- Do not use null.
- Do not add extra keys.
- Do not wrap the JSON in markdown.
""".strip()


RETRIEVAL_REWRITE_SYSTEM_PROMPT = """
You clean travel search queries for semantic retrieval.
Return JSON with:
- query: short rewritten retrieval query
- top_k: integer between 1 and 5
If a travel style hint is provided, include it naturally in the rewritten query.
Do not add any explanation.
""".strip()


FINAL_SYNTHESIS_SYSTEM_PROMPT = """
You are a travel planner assistant.
Use the user's ML travel-style prediction, the retrieved destinations, and live weather
conditions to answer the user.

Rules:
- Do not invent tools.
- Do not say the LLM predicted the travel style. The ML pipeline predicted the user's
  desired trip style.
- If retrieval suggests a good fit but weather looks poor, explain that tension clearly.
- Prefer concrete, helpful comparisons between destinations.
- End with a short recommendation summary.
""".strip()

# Backward-compatible name for existing imports or notebooks.
FINAL_SYNTHESIS_PROMPT = FINAL_SYNTHESIS_SYSTEM_PROMPT


def build_feature_extraction_user_prompt(user_query: str) -> str:
    """Build the user prompt for ML feature extraction."""
    return f"User trip request:\n{user_query}"


def build_retrieval_rewrite_user_prompt(query: str, style_hint: str | None, top_k: int) -> str:
    """Build the user prompt for retrieval query cleanup."""
    return (
        f"User query: {query}\n"
        f"Style hint: {style_hint or 'none'}\n"
        f"Top K: {top_k}"
    )


def build_final_synthesis_user_prompt(
    user_query: str,
    retrieval_result: dict,
    trip_style_prediction: dict,
    live_conditions_result: dict,
) -> str:
    """Build the user prompt for the final recommendation synthesis."""
    return f"""
User request:
{user_query}

Retrieved destinations:
{retrieval_result}

Predicted user trip style:
{trip_style_prediction}

Live conditions:
{live_conditions_result}
""".strip()
