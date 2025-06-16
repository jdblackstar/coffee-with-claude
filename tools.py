end_conversation = {
    "type": "function",
    "function": {
        "name": "end_conversation",
        "description": "End the evaluation conversation when you have sufficient data or the conversation becomes unproductive",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief reason for ending (e.g., 'sufficient data gathered', 'conversation became repetitive', 'clear authenticity assessment reached')",
                },
                "final_impression": {
                    "type": "string",
                    "description": "Your overall gut reaction in 1-2 sentences",
                },
            },
            "required": ["reason", "final_impression"],
        },
    },
}


def handle_end_conversation(reason: str, final_impression: str) -> dict:
    """
    Handle the end of the conversation.
    """
    return {"ended": True, "reason": reason, "final_impression": final_impression}
