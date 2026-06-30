STUDY_BUDDY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": (
                "Search the ingested study notes for content relevant to a topic or question. "
                "Returns the most relevant passages from the user's actual documents. "
                "Always call this before answering any content question — "
                "do not rely on general training knowledge alone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic or question to search for. Be specific."
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of passages to retrieve. Default 4, max 8.",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": (
                "Generate quiz questions on a specific topic from the user's notes. "
                "Use this when the user asks to be tested or quizzed. "
                "Always retrieve relevant material first with search_notes before generating questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to quiz on"
                    },
                    "question_type": {
                        "type": "string",
                        "enum": ["multiple_choice", "short_answer", "true_false"],
                        "description": "Format of quiz questions"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Difficulty level"
                    },
                    "n_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate. Default 3.",
                        "default": 3
                    }
                },
                "required": ["topic", "question_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_quiz_result",
            "description": (
                "Record whether the user answered a quiz question correctly. "
                "Call this after the user responds to each quiz question. "
                "This updates their long-term performance record."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "correct": {"type": "boolean"}
                },
                "required": ["topic", "correct"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weak_topics",
            "description": (
                "Get a list of topics the user has struggled with in past sessions. "
                "Use this at the start of a session to suggest what to review, "
                "or when generating an adaptive quiz."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    }
]