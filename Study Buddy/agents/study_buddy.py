import os, json
from openai import OpenAI
from dotenv import load_dotenv

from retrieval.retriever import retrieve, build_context
from memory.conversation import ConversationMemory
from memory.user_state import UserState
from tools.schemas import STUDY_BUDDY_TOOLS
from api.schemas import ChatResponse, QuizModel

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = "openrouter/free"

SYSTEM_PROMPT_TEMPLATE = """
You are a personalized study assistant. You help students understand their course material 
by answering questions, explaining concepts, and running adaptive quizzes.

USER PROFILE:
{user_profile}

RULES:
1. When answering content questions, ALWAYS call search_notes first and base your answer 
   on what you retrieve. If the notes don't cover something, say so clearly rather than 
   guessing from general knowledge.
2. When the user asks to be quizzed, call generate_quiz.
3. When citing information, mention the source document and page number from the retrieved chunk.
4. Adjust your explanation depth based on what the user profile says about their weak areas.
"""

def generate_agent_response(user_id: str, session_id: str, user_message: str) -> ChatResponse:
    user_state = UserState.load(user_id)
    conv_memory = ConversationMemory(session_id=session_id, max_tokens=3000)
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        user_profile=user_state.get_summary_for_agent()
    )
    
    conv_memory.add("user", user_message)
    messages = conv_memory.get_messages_for_api(system_prompt)
    
    quiz_data = None
    quiz_triggered = False
    
    def dispatch_tool(tool_name: str, args: dict) -> str:
        nonlocal quiz_data, quiz_triggered
        
        if tool_name == "search_notes":
            chunks = retrieve(
                args["query"],
                user_id=user_id,
                n_results=args.get("n_results", 4)
            )
            if not chunks:
                return "No relevant content found in the study notes for this query."
            context = build_context(chunks, max_tokens=2000)
            return f"Retrieved {len(chunks)} passages:\n\n{context}"
        
        elif tool_name == "generate_quiz":
            chunks = retrieve(args["topic"], user_id=user_id, n_results=5)
            if not chunks:
                return f"No notes found on '{args['topic']}'. Cannot generate questions."
            
            context = build_context(chunks, max_tokens=1500)
            difficulty = args.get("difficulty", "medium")
            q_type = args["question_type"]
            n = args.get("n_questions", 3)
            
            quiz_prompt = (
                f"Based ONLY on this material:\n\n{context}\n\n"
                f"Generate {n} {difficulty} {q_type} questions about {args['topic']}. "
                "Format as JSON array: "
                '[{"question": "...", "options": ["..."], "answer": "...", "explanation": "..."}]'
                "\nReturn ONLY the JSON array, no other text."
            )
            
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            
            raw = response.choices[0].message.content or "[]"
            try:
                raw = raw.strip().strip("```json").strip("```").strip()
                questions = json.loads(raw)
                quiz_triggered = True
                quiz_data = QuizModel(topic=args["topic"], questions=questions)
                return "Quiz successfully generated and passed to the frontend."
            except json.JSONDecodeError:
                return f"Failed to generate questions. Raw output:\n{raw}"
        
        elif tool_name == "get_weak_topics":
            weak = user_state.get_weak_topics()
            if not weak:
                return "No weak topics identified yet."
            lines = [f"- {t.topic}: {t.accuracy:.0%} accuracy ({t.times_quizzed} attempts)"
                     for t in sorted(weak, key=lambda x: x.accuracy)]
            return "Topics needing review:\n" + "\n".join(lines)
        
        return f"Unknown tool: {tool_name}"

    final_response_text = ""
    for _ in range(15):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            tools=STUDY_BUDDY_TOOLS, # type: ignore
            messages=messages # type: ignore
        )
        
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        
        if finish_reason == "stop":
            final_response_text = msg.content or ""
            conv_memory.add("assistant", final_response_text)
            break
        
        if finish_reason == "tool_calls":
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            })
            
            for tc in msg.tool_calls: # type: ignore
                args = json.loads(tc.function.arguments) # type: ignore
                result = dispatch_tool(tc.function.name, args) # type: ignore
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
    else:
        final_response_text = "Something went wrong — max tool iterations hit."
        conv_memory.add("assistant", final_response_text)

    # Save user state if updated
    user_state.save()

    return ChatResponse(
        response=final_response_text,
        quiz_triggered=quiz_triggered,
        quiz_data=quiz_data
    )