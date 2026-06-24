def calculator(expression: str) -> str:
    """
    A simple calculator that evaluates a mathematical expression.
    For a beginner, we use eval(), but in production, you should use a safer parser!
    """
    try:
        # Evaluate the mathematical expression
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"
