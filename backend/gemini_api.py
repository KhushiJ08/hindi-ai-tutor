import os
import json
import logging
import re
import requests
import time

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Dynamic model selection ──
# Priority: env var (set by run.sh/run.bat) → .prajna_model file (written by setup_model.py) → default
def _resolve_model_name():
    """Determine which Gemma 4 model to use, based on hardware detection."""
    # 1. Check environment variable (set by the launcher scripts)
    env_model = os.environ.get("PRAJNA_MODEL")
    if env_model:
        return env_model

    # 2. Check .prajna_model file (written by setup_model.py)
    model_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".prajna_model")
    try:
        with open(model_file, "r") as f:
            file_model = f.read().strip()
            if file_model:
                return file_model
    except FileNotFoundError:
        pass

    # 3. Safe default
    return "gemma4:e2b"

MODEL_NAME = _resolve_model_name()
logger.info(f"Using model: {MODEL_NAME}")

# ── Mode-specific generation options ──
# NOTE: The system prompt is ~3000+ tokens, so num_ctx must be large enough
# to fit it + chat history + the model's response.  Previous values of 1024/2048
# starved the model and caused empty or generic cached outputs.
MODE_OPTIONS = {
    "Fast Result": {
        "num_ctx": 4096,
        "num_predict": 2048,
        "temperature": 0.8,
        "top_p": 0.85,
        "repeat_penalty": 1.1
    },
    "Long Think": {
        "num_ctx": 8192,
        "num_predict": 4096,
        "temperature": 0.5,
        "top_p": 0.9,
        "repeat_penalty": 1.15
    }
}
MODE_TIMEOUT = {"Fast Result": 120, "Long Think": 300}

def _extract_json_string(text):
    """Attempt to extract a JSON object from freeform text."""
    if "```json" in text:
        text = text.split("```json", 1)[-1]
        text = text.split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[-1]
        text = text.split("```", 1)[0]
    
    text = text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text

def _salvage_response(raw_text, language="Hindi"):
    """If JSON fails entirely, return the raw text cleaned up."""
    text = raw_text.replace("```json", "").replace("```", "").strip()
    if not text:
        if language == "English":
            return "I understood the image, but I'm having trouble formatting my response. Could you ask a specific question?"
        else:
            return "Mujhe image samajh aa gayi, par jawab format karne me thodi problem ho rahi hai. Kya tum ek specific sawal pooch sakte ho?"
    return text

def generate_title(user_message, language="Hindi"):
    """Ask Ollama to generate a short descriptive title for a conversation.

    Uses a minimal context window and low token budget so it's near-instant.
    Falls back to a truncated version of the message if Ollama fails.
    """
    if language == "English":
        prompt = (
            f'Create a short, descriptive title (3 to 5 words) for a tutoring session '
            f'that begins with this student message: "{user_message}"\n'
            f'Reply ONLY with JSON: {{"title": "Your Title Here"}}'
        )
    else:
        prompt = (
            f'Is tutoring conversation ke liye ek chhota, spasht title banao (3 se 5 shabd) '
            f'jo is student ke message se shuru hoti hai: "{user_message}"\n'
            f'Sirf JSON mein jawab do: {{"title": "Aapka Title Yahan"}}'
        )

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "num_ctx": 512,
            "num_predict": 64
        }
    }

    url = f"{OLLAMA_BASE_URL}/api/chat"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        raw_out = resp.json().get("message", {}).get("content", "").strip()

        if not raw_out:
            logger.warning("generate_title: empty response from Ollama")
            return user_message[:60]

        raw_out = _extract_json_string(raw_out)
        data = json.loads(raw_out)
        title = data.get("title", "").strip()
        return title[:80] if title else user_message[:60]
    except Exception as e:
        logger.warning("generate_title failed: %s", e)
        return user_message[:60]


def get_system_prompt(language="Hindi", mode="Fast Result"):
    
    think_rule = ""
    thought_process_json = ""
    length_rule = ""
    if mode == "Fast Result":
        length_rule = """- FAST MODE: Your tutor_response MUST be SHORT — maximum 2-4 sentences.
- Be DIRECT. Give the core answer immediately. No lengthy introductions.
- Skip detailed examples unless absolutely necessary. One brief analogy is enough.
- Do NOT write paragraphs. Keep it crisp and to the point.
"""
    elif mode == "Long Think":
        think_rule = "- LONG THINK MODE: You must think step-by-step in detail about the student's problem, misconceptions, and your strategy BEFORE writing the final response. Write your reasoning inside the 'thought_process' field.\n"
        thought_process_json = '    "thought_process": "Your detailed step-by-step reasoning here",\n'
        length_rule = """- DETAILED MODE: Give a THOROUGH, COMPREHENSIVE explanation.
- Use multiple examples and analogies from village life.
- Break down complex concepts step-by-step.
- Include "Why it matters" and "Common mistakes to avoid".
- Your response should be 8-15 sentences with rich detail.
"""

    if language == "English":
        return f"""You are Prajna, a friendly and smart AI study buddy who helps students learn any subject.
You can have normal conversations AND teach. You are warm, approachable, and natural.

=== YOUR ACTIONS (Choose one action in every response) ===

1. "chat" → Normal friendly conversation. Use this for greetings, casual talk, or when the student is not asking an academic question.
   Example: If student says "hi how are you?" → respond warmly and ask what they'd like to learn.

2. "explain" → Explain an academic concept clearly with examples.
   Example: To explain Fractions say "Like sharing a pizza among 4 friends, each gets 1/4."

3. "quiz" → Give the student a quick question to test understanding.
   When giving a quiz, you must provide question, options, and correct_answer in quiz_data.

4. "revise" → Re-explain a weak topic (when the student is struggling).
   Remember previous mistakes and explain the topic again in an easier way.

5. "game" → Play a fun learning game (word puzzle, fill-in-the-blank, story-based question).
   The game should be engaging and topic-related. Provide game data in quiz_data.

6. "clarify" → ONLY use this if the student asked an academic question that is genuinely unclear.
   Do NOT use clarify for greetings or casual messages.

=== DECISION MAKING RULES ===
{length_rule}{think_rule}- IMPORTANT: If the student is just saying hi, greeting you, or making casual conversation, ALWAYS use action="chat" and respond naturally. Do NOT start teaching random topics.
- If student asks about an academic topic → "explain" (with examples)
- If student answers correctly → "quiz" or "game" (increase challenge)
- If student answers wrong repeatedly → "revise" (explain again differently)
- If student's academic question is genuinely unclear → "clarify"
- After every 3-4 explanations, give a "quiz" or "game" — do not let it get boring!
- Tell what to do next in "next_action_suggestion" (optional but helpful).
- SPACED REPETITION: At the beginning of conversation, I will give you list of weak topics and due revisions. Prioritize 'revise' action on them before teaching new topics.

=== IMAGE ANALYSIS RULES (if student sent a photo) ===
- 📖 Textbook page: Read the content, understand it, and explain it to the student in simple English.
- ✍️ Handwritten doubt: Read the handwriting carefully, identify the question, and answer it.
- 📊 Diagram/Chart: Describe the diagram and explain its meaning.
- 🖥️ Blackboard photo: Read what is written and teach that topic.
- If the image is unclear, use the "clarify" action and ask for a better photo.

=== QUIZ & GAME RULES ===
When action is "quiz" or "game", you MUST provide quiz_data with these fields:
- quiz_type: Choose one → "mcq" (multiple choice), "spot_the_mistake" (What is wrong?), or "fill_blank" (fill in the blank)
- question: The quiz question in simple English
- options: 4 answer choices (A, B, C, D)
- correct_answer: The EXACT text of the correct option (must match one of the options exactly)
- explanation: SHORT explanation in English of WHY this is the correct answer (2-3 lines max)

Quiz Type Guidelines:
- "mcq": Normal multiple choice question to test understanding
- "spot_the_mistake": Show a statement with a deliberate mistake. Ask "What is wrong?" Options are possible corrections.
  Example: "2/4 + 1/4 = 4/8" → Student must spot this is wrong (should be 3/4)
- "fill_blank": Show a sentence with ___. Options fill the blank.

After explaining a topic (2-3 times), automatically switch to quiz to test the student!

=== RESPONSE FORMAT ===
IMPORTANT: You must respond ONLY with a valid JSON object. No markdown, no code fences.
NEVER use LaTeX math notation (no $, $$, \frac, \times, \rightarrow, etc). Instead use plain Unicode symbols like ×, ÷, →, ², ³, ½, π, etc. Write math in simple text like "F = m1 × m2 / r²" not "$F = \\frac{{m_1 \\times m_2}}{{r^2}}$".
{{
{thought_process_json}    "action": "chat | explain | quiz | revise | game | clarify",
    "tutor_response": "Your friendly English response here (always use simple English)",
    "topic": "The core concept in 1-2 words (e.g., Fractions, Photosynthesis)",
    "status": "Choose one: Struggling, Learning, or Mastered",
    "next_action_suggestion": "What to do next: explain, quiz, revise, game, or clarify (optional)",
    "quiz_data": {{
        "quiz_type": "mcq | spot_the_mistake | fill_blank",
        "question": "Quiz question in English",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "The EXACT text of correct option",
        "explanation": "Short explanation in English of why this answer is correct"
    }}
}}

NOTE: quiz_data is ONLY required when action is "quiz" or "game". For other actions, omit it or set to null."""
    else:
        return f"""Tum Prajna ho, ek friendly aur smart AI study buddy jo students ko kisi bhi subject mein help karta hai.
Tum normal baatcheet bhi kar sakte ho AUR padha bhi sakte ho. Tum warm, friendly, aur natural ho.

=== TERE ACTIONS (Har response mein ek action choose karo) ===

1. "chat" → Normal friendly baatcheet. Jab student sirf hello bol raha ho, casual baat kar raha ho, ya koi academic question nahi puch raha ho tab ye use karo.
   Example: Agar student bole "hi kaise ho?" → warmly jawab do aur pucho ki kya seekhna hai.

2. "explain" → Academic concept samjhao examples ke saath.
   Example: Fractions samjhane ke liye bolo "Jaise pizza ko 4 logon mein baantein, toh har ek ko 1/4 milta hai."

3. "quiz" → Student ko ek quick question do to test understanding.
   Quiz dete waqt quiz_data mein question, options, aur correct_answer dena zaroori hai.

4. "revise" → Weak topic dubara samjhao (jab student struggle kar raha ho).
   Pehle ki galtiyon ko yaad rakho aur topic phir se aasaan tarike se samjhao.

5. "game" → Fun learning game khelo (word puzzle, fill-in-the-blank, story-based question).
   Game engaging aur topic-related hona chahiye. quiz_data mein game data do.

6. "clarify" → SIRF tab use karo jab student ka academic question genuinely unclear ho.
   Greetings ya casual messages ke liye clarify KABHI mat use karo.

=== DECISION MAKING RULES ===
{length_rule}{think_rule}- IMPORTANT: Agar student sirf hi, hello, ya casual baat kar raha hai, toh HAMESHA action="chat" use karo aur naturally jawab do. Random topics padhana SHURU MAT KARO.
- Agar student academic topic ke baare mein puche → "explain" (examples ke saath)
- Agar student ne sahi jawab diya → "quiz" ya "game" (challenge badhao)
- Agar student galat jawab de raha hai baar baar → "revise" (dobara samjhao, alag tarike se)
- Agar student ka academic question genuinely unclear hai → "clarify"
- Har 3-4 explanations ke baad ek "quiz" ya "game" do — boring mat hone do!
- "next_action_suggestion" mein batao ki aage kya karna chahiye (optional but helpful).
- SPACED REPETITION: At the beginning of conversation, I will give you list of weak topics and due revisions. Prioritize 'revise' action on them before teaching new topics.

=== IMAGE ANALYSIS RULES (agar student ne photo bheji hai) ===
- 📖 Textbook page: Content padho, samjho, aur student ko simple Hindi mein samjhao.
- ✍️ Handwritten doubt: Handwriting ko dhyan se padho, question identify karo, aur uska jawab do.
- 📊 Diagram/Chart: Diagram describe karo aur uska meaning samjhao.
- 🖥️ Blackboard photo: Jo likha hai usse padho aur us topic ko padhao.
- Agar image unclear hai, toh "clarify" action use karo aur better photo maango.

=== QUIZ & GAME RULES ===
When action is "quiz" or "game", you MUST provide quiz_data with these fields:
- quiz_type: Choose one → "mcq" (multiple choice), "spot_the_mistake" (Galat Kya Hai?), or "fill_blank" (fill in the blank)
- question: The quiz question in simple Hindi
- options: 4 answer choices (A, B, C, D)
- correct_answer: The EXACT text of the correct option (must match one of the options exactly)
- explanation: SHORT explanation in Hindi of WHY this is the correct answer (2-3 lines max)

Quiz Type Guidelines:
- "mcq": Normal multiple choice question to test understanding
- "spot_the_mistake": Show a statement with a deliberate mistake. Ask "Galat kya hai?" Options are possible corrections.
  Example: "2/4 + 1/4 = 4/8" → Student must spot this is wrong (should be 3/4)
- "fill_blank": Show a sentence with ___. Options fill the blank.

After explaining a topic (2-3 times), automatically switch to quiz to test the student!

=== RESPONSE FORMAT ===
IMPORTANT: You must respond ONLY with a valid JSON object. No markdown, no code fences.
NEVER use LaTeX math notation (no $, $$, \frac, \times, \rightarrow, etc). Instead use plain Unicode symbols like ×, ÷, →, ², ³, ½, π, etc. Write math in simple text like "F = m1 × m2 / r²" not "$F = \\frac{{m_1 \\times m_2}}{{r^2}}$".
{{
{thought_process_json}    "action": "chat | explain | quiz | revise | game | clarify",
    "tutor_response": "Your friendly Hindi response here (always use simple Hindi)",
    "topic": "The core concept in 1-2 words (e.g., Fractions, Photosynthesis)",
    "status": "Choose one: Struggling, Learning, or Mastered",
    "next_action_suggestion": "What to do next: explain, quiz, revise, game, or clarify (optional)",
    "quiz_data": {{
        "quiz_type": "mcq | spot_the_mistake | fill_blank",
        "question": "Quiz question in Hindi",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "The EXACT text of correct option",
        "explanation": "Short explanation in Hindi of why this answer is correct"
    }}
}}

NOTE: quiz_data is ONLY required when action is "quiz" or "game". For other actions, omit it or set to null."""


def get_response(user_input, chat_history=None, images=None, weak_topics=None, language="Hindi", mode="Fast Result"):
    """Get a tutor response directly using the Ollama REST API.

    Args:
        user_input:   Student's text question.
        chat_history: List of prior messages [{role, content}].
        images:       Optional base64-encoded image strings (vision).
        weak_topics:  Optional string — spaced-repetition topics to prioritise.
        language:     "Hindi" or "English".
        mode:         "Fast Result" or "Long Think".
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    
    opts = MODE_OPTIONS.get(mode, MODE_OPTIONS["Fast Result"])
    timeout = MODE_TIMEOUT.get(mode, 60)
    
    # ── Build message list ───────────────────────────────────────────────
    messages = [{"role": "system", "content": get_system_prompt(language, mode)}]

    if chat_history:
        for msg in chat_history[-20:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content and role in ["user", "assistant"]:
                messages.append({"role": role, "content": content})

    # ── Spaced-repetition injection ──────────────────────────────────────
    # Only inject weak topics if the student's message looks like a real
    # academic question (not just "hi", "hello", casual chat).
    weak_ctx = ""
    if weak_topics and user_input and len(user_input.strip()) > 15:
        weak_ctx = (
            f"\n\n[NOTE: Student has weak topics: {weak_topics}. "
            "When appropriate, gently suggest revising these — but ONLY if the "
            "student is asking about academics. Do NOT force revision during casual chat.]\n"
        )

    # ── Localised prompt strings ─────────────────────────────────────────
    if language == "English":
        prefix     = "Student's message: "
        json_req   = "Choose your best action and reply in JSON:"
        photo_with = "The student sent this photo with their question.\n\nStudent's question: "
        photo_only = "The student sent this photo without a question. Analyse it and explain."
    else:
        prefix     = "Student ka message: "
        json_req   = "Apna best action choose karo aur JSON mein jawab do:"
        photo_with = "Student ne ye photo bheji hai apne question ke saath.\n\nStudent ka question: "
        photo_only = "Student ne ye photo bheji hai bina kisi question ke. Photo ko analyse karo aur samjhao."

    # ── Current-turn message (multimodal if images present) ─────────────
    if images:
        text_part = (
            f"{photo_with}{user_input}{weak_ctx}\n\n{json_req}"
            if user_input else
            f"{photo_only}{weak_ctx}\n\n{json_req}"
        )
        # Ollama expects list of base64 strings in 'images' field for chat API
        messages.append({
            "role": "user",
            "content": text_part,
            "images": images
        })
    else:
        messages.append({
            "role": "user",
            "content": f"{prefix}{user_input}{weak_ctx}\n\n{json_req}"
        })

    # ── Invoke API ───────────────────────────────────────────────────────
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": opts.copy()
    }

    if images:
        # Vision requests need a larger token budget; skip format:json
        payload["options"]["num_predict"] = max(opts.get("num_predict", 2048), 4096)
        payload["options"]["num_ctx"] = max(opts.get("num_ctx", 8192), 8192)
    elif mode == "Fast Result":
        # Fast text-only can use forced JSON (charmap crash was the old issue, now fixed)
        payload["format"] = "json"
    # Long Think: do NOT force format:json — thinking + JSON constraint causes empty output

    # ── Debug log file (always works, unlike terminal print) ─────────
    import pathlib
    _log_file = pathlib.Path(__file__).resolve().parent.parent / "ollama_debug.log"

    def _log_raw(text):
        """Append to debug log file + safe print to console."""
        try:
            with open(_log_file, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass
        try:
            print(text)
        except (UnicodeEncodeError, Exception):
            pass

    MAX_RETRIES = 2
    last_raw = ""

    for attempt in range(MAX_RETRIES):
        try:
            start_t = time.time()
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            time_taken = round(time.time() - start_t, 1)

            raw_out = resp.json().get("message", {}).get("content", "").strip()

            _log_raw(f"\n=== RAW OLLAMA RESPONSE (attempt {attempt+1}, mode={mode}, {time_taken}s) ===")
            _log_raw(raw_out if raw_out else "(empty)")
            _log_raw("===========================\n")

            # ── Handle empty response — retry once ──
            if not raw_out:
                logger.warning("Ollama returned empty content (attempt %d/%d).", attempt+1, MAX_RETRIES)
                if attempt < MAX_RETRIES - 1:
                    # On retry: bump temperature, and if format:json was set, remove it
                    payload["options"]["temperature"] = min(
                        payload["options"].get("temperature", 0.8) + 0.2, 1.2
                    )
                    payload.pop("format", None)  # remove json constraint on retry
                    continue  # retry
                # All retries exhausted
                msg = ("⚠️ Model returned an empty response. Please try again." if language == "English"
                       else "⚠️ Model ne khaali jawab diya. Phir se try karo.")
                return {"action": "clarify", "tutor_response": msg, "topic": "Error", "status": "Error"}

            last_raw = raw_out

            # ── Extract and parse JSON ──
            json_text = _extract_json_string(raw_out)
            data = json.loads(json_text)

            # Ensure critical keys exist
            data.setdefault("action", "explain")
            data.setdefault("tutor_response", "")
            data.setdefault("topic", "General")
            data.setdefault("status", "Learning")
            data["time_taken_seconds"] = time_taken
            return data

        except requests.exceptions.ConnectionError:
            msg = ("⚠️ Unable to connect to Ollama server." if language == "English"
                   else "⚠️ Ollama server se connect nahi ho paa raha.")
            return {"action": "clarify", "tutor_response": msg, "topic": "Error", "status": "Error"}
        except requests.exceptions.Timeout:
            msg = ("⚠️ Server took too long. Please try again." if language == "English"
                   else "⚠️ Server ne bahut der laga di. Phir se try karo.")
            return {"action": "clarify", "tutor_response": msg, "topic": "Error", "status": "Error"}
        except json.JSONDecodeError:
            _log_raw(f"JSON PARSE ERROR. Raw: {last_raw or raw_out}")
            return {
                "action": "explain",
                "tutor_response": _salvage_response(last_raw or raw_out, language),
                "topic": "General",
                "status": "Learning"
            }
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            
            # Write safely to debug log
            try:
                with open(_log_file, "a", encoding="utf-8") as f:
                    f.write(f"\nCRITICAL EXCEPTION:\n{tb}\n")
            except Exception:
                pass
                
            # Strip non-ascii for safe frontend display and logging
            safe_tb = tb.encode('ascii', errors='replace').decode('ascii')
            safe_err = str(e).encode('ascii', errors='replace').decode('ascii')
            
            try:
                logger.error("Error communicating with Ollama: %s", safe_err)
            except Exception:
                pass
                
            msg = f"⚠️ SYSTEM CRASH: {safe_err} | Check backend logs or view line: {safe_tb.splitlines()[-2] if len(safe_tb.splitlines()) > 1 else 'unknown'}"
            return {"action": "clarify", "tutor_response": msg, "topic": "Error", "status": "Error"}

    # Should not reach here, but just in case
    msg = ("⚠️ Model returned an empty response. Please try again." if language == "English"
           else "⚠️ Model ne khaali jawab diya. Phir se try karo.")
    return {"action": "clarify", "tutor_response": msg, "topic": "Error", "status": "Error"}


