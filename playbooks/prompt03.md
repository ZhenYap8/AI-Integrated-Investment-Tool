# Prompt 03: AI-Driven Pros & Cons Analysis

## Overview
This prompt logic drives the `analyze_proscons_ai_only` service, which generates a balanced list of investment pros and cons for a given ticker using OpenAI (GPT-4).

## Workflow
1.  **Context Building** (`context.py`):
    *   Fetches Yahoo Finance data:
        *   Key statistics (P/E, Margins, Beta, Cashflow).
        *   Recent price performance (1mo, 3mo, 6mo, 1y).
        *   Recent news headlines and abstracts (via `trafilatura`).
    *   Constructs a text blob summarizing the company's current state.

2.  **LLM Extraction** (`llm.py`):
    *   **System Prompt**: Acts as an equity analyst.
    *   **Goal**: Extract 2-3 sentence causal findings (mechanism + why it matters).
    *   **Constraints**:
        *   Avoid generic boilerplate ("Strong top-line growth").
        *   Must cite specific metrics or events from the context.
        *   Must include evidence (URL, date, snippet).
    *   **Parameters**: Temperature 0.1 (deterministic), JSON mode.

3.  **Filtering & Validation** (`filters.py`):
    *   **Banned Phrases**: Removes generic fluff like "robust fundamentals".
    *   **Causal Check**: Ensures findings contain causal keywords ("because", "driven by").
    *   **Number Consistency**: Verifies that numbers in the finding match numbers in the evidence snippets (hallucination check).
    *   **Deduplication**: Removes semantically similar findings using set intersection logic.

4.  **Orchestration** (`orchestrator.py`):
    *   Initial pass: Asks for mixed Pros & Cons.
    *   **Cons Top-up**: If too few cons are returned, triggers a second LLM call focused specifically on "CONS".
    *   **Fallback**: If LLM fails or returns nothing, falls back to rule-based logic using raw Yahoo Finance stats (`fallback.py`).
    *   **Balancing**: Ensures a roughly even mix of Pros and Cons in the final output.

## Key Files
*   `IBBack/services/prosandcons/orchestrator.py`: Main entry point.
*   `IBBack/services/prosandcons/llm.py`: Prompt engineering and API calls.
*   `IBBack/services/prosandcons/context.py`: Data gathering.
*   `IBBack/services/prosandcons/filters.py`: Quality control regexes.
