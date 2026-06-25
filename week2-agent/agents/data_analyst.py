import os, json
from openai import OpenAI
from dotenv import load_dotenv
from sandbox.namespace import PersistentNamespace
from tools.Schemas import DATA_ANALYST_TOOLS
from tools.analysis_tools import describe_csv
from agents.prompts import DATA_ANALYST_SYSTEM

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"



class DataAnalystAgent:
    def __init__(self):
        self.session = PersistentNamespace()
        self.conversation: list[dict] = [
            {"role": "system", "content": DATA_ANALYST_SYSTEM}
        ]
    
    def _dispatch(self, tool_name: str, args: dict) -> str:
        if tool_name == "describe_csv":
            return describe_csv(args["filepath"])
        
        elif tool_name == "execute_analysis":
            result = self.session.execute(args["code"])
            response = result.to_tool_string()
            # Append session state so agent always knows what's in scope
            if result.success and result.local_vars:
                response += f"\n\nSession variables now in scope: {list(result.local_vars.keys())}"
            return response
        
        elif tool_name == "get_session_state":
            vars_in_scope = self.session.get_defined_vars()
            if not vars_in_scope:
                return "Session is empty — no variables defined yet."
            return f"Variables currently in scope: {vars_in_scope}"
        
        elif tool_name == "reset_session":
            self.session.reset()
            return "Session cleared. All variables removed."
        
        return f"Unknown tool: {tool_name}"
    
    def chat(self, user_message: str) -> str:
        """Send one user message and run the agent loop until it responds."""
        self.conversation.append({"role": "user", "content": user_message})
        
        for _ in range(20):  # max tool calls per user message
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                tools=DATA_ANALYST_TOOLS,
                messages=self.conversation # type: ignore
            )
            
            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            
            if msg.content:
                print(f"\n💭 {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            
            if finish_reason == "stop":
                self.conversation.append({
                    "role": "assistant",
                    "content": msg.content
                })
                return msg.content or ""
            
            if finish_reason == "tool_calls":
                self.conversation.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls
                })
                
                for tc in msg.tool_calls: # type: ignore
                    args = json.loads(tc.function.arguments) # type: ignore
                    print(f"\n🔧 {tc.function.name}({str(args)[:80]})") # type: ignore
                    
                    result = self._dispatch(tc.function.name, args) # type: ignore
                    print(f"   → {result[:200]}{'...' if len(result) > 200 else ''}")
                    
                    self.conversation.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
        
        return "Max iterations reached for this message."


def run_interactive_session():
    """Multi-turn REPL for data analysis."""
    agent = DataAnalystAgent()
    print("Data Analyst Agent — type 'quit' to exit, 'reset' to clear session\n")
    
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            agent = DataAnalystAgent()
            print("Session reset.")
            continue
        
        answer = agent.chat(user_input)
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    run_interactive_session()