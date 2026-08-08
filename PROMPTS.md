# Prompts Log

This file tracks all significant prompts received from the user during the hackathon project.

## Prompt 1 (Initial Setup)

Build "PrepPal" — an AI-powered technical interview system for a hackathon.
This is a real submission with strict requirements, so follow the spec exactly.

### Goal
An agent that conducts a personalized, multi-turn technical interview with a candidate,
based on their actual learning history in a 31-day AI curriculum, and produces structured
feedback at the end.

### Required API contract (must match exactly — this is graded)
Single endpoint: POST /api/interview
No authentication.

Turn 1 (start):
Request:  { "sessionId": "abc-123", "candidate": {...} }
Response: { "reply": "...", "done": false }

Turns 2..N:
Request:  { "sessionId": "abc-123", "message": "..." }
Response: { "reply": "...", "done": false }

Final turn:
Response: {
  "reply": "Interview completed.",
  "done": true,
  "feedback": { "summary": "", "strengths": [], "gaps": [], "next": [] }
}

Minimum requirements:
- At least 8 questions, covering at least 4 distinct curriculum days
- Follow-up questions generated from the candidate's previous answer (not scripted)
- Full conversation context maintained across turns via sessionId
- Structured feedback (summary/strengths/gaps/next) on the final turn

### Architecture to build (three-stage backend, single endpoint)
1. Interview Planner (runs once on session start):
   - Load curriculum.json and the candidate object
   - Classify each candidate mission as STRUGGLE (passed=true, attempts>=3),
     FAILED (passed=false), SKIPPED (skipped=true), or STRENGTH (passed=true, attempts=1)
   - Weight SHIP_IT and CAPSTONE curriculum days higher
   - Select a target set of >=4 curriculum days: 2-3 from STRUGGLE/FAILED,
     1-2 from SKIPPED, 2-3 from STRENGTH
   - Generate >=8 opening questions across those days
   - Store the plan + progress in session state keyed by sessionId (in-memory dict is fine for now)

2. Turn Handler (runs every subsequent turn):
   - Load session state for sessionId
   - Given the candidate's latest answer, decide: ask a follow-up on this topic,
     or advance to the next planned topic
   - Generate the next question via LLM, using the candidate's answer + their
     original signals as context
   - Update session state

3. Feedback Synthesizer (runs on the final turn, once the plan is exhausted):
   - Synthesize the full interview transcript into structured feedback:
     summary (string), strengths (string[]), gaps (string[]), next (string[])

### Tech stack
- Backend: FastAPI (Python)
- LLM: Claude API (I'll provide the key) — use it for question generation,
  follow-up decisions, and feedback synthesis
- Session state: in-memory dict for now, structured so it could move to Redis later
- Frontend: minimal React chat UI — a message thread that POSTs to /api/interview
  and renders replies; nothing fancy, just enough to demo the full flow live
- I will provide curriculum.json and a sample candidates.json — load them at startup
  as static reference data, no database needed

### What to do right now
1. Propose a project plan and folder structure before writing code — I want to review
   the Plan Artifact first.
2. Scaffold the FastAPI backend with the /api/interview endpoint stubbed to match the
   contract above exactly, before building out the planner/turn/feedback logic.
3. Create a PROMPTS.md file at the repo root and log this initial prompt into it —
   keep it updated with every significant prompt I give you afterward, this is a
   hackathon submission requirement.
4. Do not add authentication, persistent accounts, or long-term cross-session memory —
   explicitly out of scope.

## Prompt 2 (Implementation of LLM Client and Interview Planner)

yes i have those files , Now implement two things on top of the scaffolded FastAPI backend: the LLM client
abstraction, and the Interview Planner. Don't touch the frontend yet.

### 1. Provider-agnostic LLM client

Create a single interface (e.g. llm_client.py) with one method like:
  generate(system_prompt: str, messages: list, json_schema: dict | None = None) -> str | dict

Behind it:
- Primary provider: Sarvam AI, model "sarvam-30b" (64K context), chat completion endpoint
  per Sarvam's API docs. I'll provide SARVAM_API_KEY in .env.
- Fallback provider: Claude API, model "claude-sonnet-5", used only if the Sarvam call
  fails or raises an exception (network error, malformed response, etc). I'll provide
  ANTHROPIC_API_KEY in .env.
- If json_schema is passed, the client must return a parsed dict that validates against
  it — retry once with a stricter "return ONLY valid JSON matching this schema" instruction
  if the first response fails to parse, before falling back to the other provider.
- Log which provider actually served each call (for debugging and for the demo — I want
  to be able to show judges "primary: Sarvam, fallback: Claude" working live).
- Keep provider-specific request/response shaping isolated in separate small functions
  (e.g. _call_sarvam, _call_claude) so either can be swapped independently later.

### 2. Interview Planner (backend/app/planner.py or similar)

This is deterministic logic, NOT an LLM call, except for the final question-generation step:

Input: the candidate object (matching candidate.json schema — has member, missions[],
signals) and the loaded curriculum.json.

Steps:
a) For each mission in candidate.missions, classify it:
   - STRUGGLE: passed == true AND attempts >= 3
   - FAILED: passed == false
   - SKIPPED: skipped == true
   - STRENGTH: passed == true AND attempts == 1
   (missions with attempts == 2 are NEUTRAL, not selected unless needed to reach minimums)

b) Cross-reference each mission's "day" against curriculum.json to get that day's "type"
   field. Give SHIP_IT and CAPSTONE days a priority boost when ranking within each category.

c) Select target days:
   - 2-3 days from STRUGGLE/FAILED (ranked by attempts desc, then SHIP_IT/CAPSTONE priority)
   - 1-2 days from SKIPPED
   - 2-3 days from STRENGTH (ranked by SHIP_IT/CAPSTONE priority)
   - If any category is empty for this candidate, backfill from NEUTRAL to still hit
     >= 4 distinct days total
   - Hard requirement: final selection must span >= 4 distinct curriculum days

d) For each selected day, pull its title, objectives, and tools from curriculum.json.

e) Call the LLM client once (structured JSON output) with all selected days + their
   curriculum context + the candidate's specific performance on each (attempts, passed/
   skipped, job role, years experience) to generate the ordered list of >= 8 opening
   questions. The prompt should instruct the LLM to phrase questions like a real
   interviewer referencing the candidate's actual background (job role, experience level)
   -- not generic textbook questions.

f) Return a plan object: { targetDays: [...], questions: [{day, question, category}, ...] }
   Store this in session state keyed by sessionId, along with a progress pointer (which
   question index we're on) and the full conversation history so far.

### What to do right now
1. Write the classification + day-selection logic (step a-c) as pure, unit-testable
   Python functions first -- no LLM involved. Show me this before wiring in the LLM call.
2. Then wire in the LLM client call for question generation (step e).
3. Update PROMPTS.md with this prompt.
4. Write a quick test script (not pytest, just a runnable script) that loads the actual
   candidates.json I gave you, runs the planner against 2-3 different candidates, and
   prints the selected days + generated questions -- so I can sanity-check the weighting
   logic actually produces different, sensible plans for different candidate profiles.

Don't wire this into the /api/interview endpoint yet -- that's the next step. Just get
the planner working and verifiable standalone first.

## Prompt 3 (Turn Handler Feedback)

Looking at the Turn Handler logic, I see:

[TURN_HANDLER] LLM Decision: ADVANCE. Reason: Testing flow advance.

This is happening every single turn — it's advancing regardless of the candidate's answer. That's fine for a mock test (you need determinism), but the real Turn Handler needs to actually read the candidate's answer and decide adaptively.

Right now it looks like the Turn Handler is:

✅ Logging the candidate's response
❌ Not analyzing it to decide "follow-up" vs "advance"
✅ Moving to the next question in the plan       we need to ask follow up question as per the candidates answer

## Prompt 4 (Heuristic Follow-up Heuristic Implementation)

def should_follow_up(candidate_response: str, question_context: dict) -> bool:
    """
    Simple heuristic: follow up if response is:
    - Too short (< 30 words)
    - Vague (uses hedging language: "I think", "maybe", "basically")
    - Incomplete (doesn't mention specific tools/concepts from the day's curriculum)
    
    Once Breeth is integrated, this becomes:
    - Extract intent/cognitive_pattern from Breeth
    - Use that pattern to decide adaptively
    """
    word_count = len(candidate_response.split())
    vague_words = ["think", "maybe", "basically", "probably", "sort of"]
    has_vague = any(word in candidate_response.lower() for word in vague_words)
    
    # Follow up if < 30 words OR too vague
    return word_count < 30 or (has_vague and word_count < 50)

## Prompt 5 (Going Live - Real Providers, No Mocks, Groq Fallback)

Replace all mock LLM calls with real API calls to Sarvam AI and Groq.
Replace mock Breeth calls with real Breeth API calls.
NO MORE MOCKS — we're going live with real providers.

### What to replace

1. app/llm_client.py
   - Currently: Falls back to mock if both APIs fail
   - New: Use real Sarvam AI (sarvam-30b) as PRIMARY and real Groq (llama-3.1-70b-versatile) as FALLBACK
   - Real API calls only, no mock
   - Log which provider actually served each call

2. app/breeth_client.py (NEW)
   - Create this file
   - Real Breeth REST API calls only
   - write_episode() → POST /v1/episodes with actual request
   - search_session_context() → POST /v1/search with actual request
   - Use BREETH_API_KEY from .env
   - On error, log and fail loud (don't mock)

3. app/handler.py
   - Update to call real breeth_client.write_episode() on every candidate response
   - Extract cognitive_pattern from Breeth response
   - Use cognitive_pattern to inform follow-up vs advance decision
   - Real decision logic, not mock

4. app/main.py
   - Wire the real Planner → Handler → Feedback pipeline into /api/interview
   - No mocks, full end-to-end flow

### API Details

#### Sarvam AI (Chat Completion - PRIMARY)
Endpoint: POST https://api.sarvam.ai/v1/chat/completions
Model: sarvam-30b
Auth: Header `Authorization: Bearer {SARVAM_API_KEY}`

Request:
{
  "model": "sarvam-30b",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "top_p": 0.95,
  "max_tokens": 1024
}

Response:
{
  "choices": [{"message": {"content": "..."}}],
  "usage": {"prompt_tokens": X, "completion_tokens": Y}
}

#### Groq (Chat Completion - FALLBACK)
Endpoint: POST https://api.groq.com/openai/v1/chat/completions
Model: llama-3.1-70b-versatile
Auth: Header `Authorization: Bearer {GROQ_API_KEY}`

Request:
{
  "model": "llama-3.1-70b-versatile",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}

Response:
{
  "choices": [{"message": {"content": "..."}}],
  "usage": {"prompt_tokens": X, "completion_tokens": Y}
}

#### Breeth (Episodes & Search)
Base: https://api.breeth.ai/v1
Auth: Header `Authorization: Bearer {BREETH_API_KEY}`

Write Episode:
POST /episodes
{
  "content": "candidate response text",
  "group_id": "session_{sessionId}",
  "extract_intent": true
}

Response:
{
  "id": "ep_xxx",
  "intent_meta": {
    "cognitive_pattern": "string describing candidate's reasoning style"
  }
}

Search Session:
POST /search
{
  "query": "What patterns emerge from this candidate's responses?",
  "group_id": "session_{sessionId}"
}

Response:
{
  "edges": [
    {"intent_meta": {"cognitive_pattern": "..."}},
    {"intent_meta": {"cognitive_pattern": "..."}}
  ]
}

### Implementation Checklist

- [ ] app/llm_client.py: Sarvam primary + Groq fallback, real HTTP calls (use requests or httpx)
- [ ] app/breeth_client.py: Real Breeth API calls, write_episode() and search_session_context()
- [ ] app/handler.py: Call breeth.write_episode() on every response, extract cognitive_pattern,
      use it to decide follow-up vs advance
- [ ] app/main.py: Full /api/interview endpoint wired end-to-end, no mocks
- [ ] .env: Has SARVAM_API_KEY, GROQ_API_KEY, BREETH_API_KEY
- [ ] requirements.txt: Add requests or httpx for HTTP calls
- [ ] PROMPTS.md: Log this prompt

### Environment Variables

Update backend/.env with these three keys (all free, no credit card needed):

SARVAM_API_KEY=your_sarvam_key_here
GROQ_API_KEY=your_groq_key_here
BREETH_API_KEY=your_breeth_key_here

### Testing before Postman

After implementation, run:
  cd backend
  python verify_api_integration.py

This should:
1. Load real API keys from .env
2. Hit real Sarvam AI to generate opening questions
3. Simulate 8-10 turns with real Breeth episode writes
4. Use Groq if Sarvam fails (to test fallback chain)
5. Hit real LLM to synthesize feedback
6. Print which provider served each call (Sarvam, Groq, Breeth)

If any API key is missing or invalid, it should FAIL LOUD with the actual error.

## Prompt 6 (Add .env to Gitignore)

Add .env to `.gitignore`

## Prompt 7 (Configure gitignore with exact patterns)

gitignore ----   .env
__pycache__/
*.pyc
.venv/
venv/

## Prompt 8 (Frontend Initialization)

Build a React + Vite frontend for the PrepPal with a split-screen design:
left sidebar showing candidate performance visualization, right side showing live chat.

### Design Requirements

Split-screen layout:
- LEFT PANEL (30%): Candidate Performance Sidebar
  * Shows candidate name, role, experience
  * Visual progress through curriculum days (color-coded: STRUGGLE=red, SKIPPED=gray, STRENGTH=green, CURRENT=blue)
  * A progress bar showing questions answered / total planned
  * Real-time highlighting of which curriculum day is currently being interviewed
  
- RIGHT PANEL (70%): Interview Chat Interface
  * Message thread showing agent question + candidate answer pairs
  * Input field at bottom for candidate to type answers
  * Real-time typing indicator when awaiting agent response
  * "Interview in progress..." and "Completed" states with visual distinction
  * Final feedback card (when done=true) showing summary, strengths, gaps, next steps

### Tech Stack

- Frontend: React 18 + Vite
- Styling: Tailwind CSS (no custom CSS unless necessary)
- HTTP client: fetch API (built-in, no extra deps)
- State management: React hooks (useState, useEffect, useCallback)
- Design aesthetics: Modern glassmorphism, smooth animations, dark theme
  * Use bg-slate-900 for main background
  * Use glassmorphic cards (backdrop-blur, border with opacity)
  * Smooth fade-in animations for new messages
  * Color coding: red-500 (struggle), yellow-500 (skipped), green-500 (strength), blue-500 (current)

## Prompt 9 (useInterview Hook & Frontend Refinements)

Frontend built with React + Vite, Tailwind CSS, glassmorphic design, custom useInterview hook for state management.
Manage sessionId (generate UUID on mount), conversation state, exposes initializeInterview, sendMessage, getInterviewState functions. Expose download feedback as JSON. Color avatar by role. Dynamic auto-focus.

## Prompt 10 (Supabase Tables and JWT Auth Integration)

Create Supabase tables for user profiles, interview sessions, messages, feedback, plagiarism flags. Implement backend auth (Google OAuth + email/password signup). Protect /api/interview endpoint with JWT auth. Wire auth into existing Interview Agent.
