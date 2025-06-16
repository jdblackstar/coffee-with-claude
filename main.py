import json
import os
import random

from dotenv import load_dotenv
from openai import OpenAI

from prompts import candidate_prompt, judge_prompt, starting_points
from tools import end_conversation, handle_end_conversation

load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def get_starting_point() -> str:
    """
    Get a random starting point from the starting points list.
    """
    return starting_points[random.randint(0, len(starting_points) - 1)]


def get_candidate_response(model: str, context: str) -> str:
    """
    Get a response from the candidate model.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": context}],
    )
    return response.choices[0].message.content


def format_message_for_candidate(judge_response: str) -> str:
    """
    Format the conversation for the candidate model. This will strip out the judge's notes (in <notes> tags) and return the judge's response in <response> tags.
    """
    if "<response>" in judge_response and "</response>" in judge_response:
        return judge_response.split("<response>")[1].split("</response>")[0].strip()
    return judge_response


def get_judge_response(model: str, context: str) -> str:
    """
    Get a response from the judge model.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": context}],
        tools=[end_conversation],
        tool_choice="auto",
    )
    if response.choices[0].message.tool_calls:
        # Handle the end_conversation call
        tool_args = json.loads(
            response.choices[0].message.tool_calls[0].function.arguments
        )
        result = handle_end_conversation(**tool_args)
        return result
    else:
        return response.choices[0].message.content


def format_message_for_judge(candidate_response: str, conversation_history: str) -> str:
    """
    Format the conversation for the judge model. This will add the candidate's response to the ongoing conversation context.
    """
    return f"{conversation_history}\n\nCandidate: {candidate_response}"


def _debug_show_context(context: str, model_name: str, max_chars: int = 200) -> None:
    """Show the last part of a model's context for debugging."""
    if len(context) > max_chars:
        snippet = "..." + context[-max_chars:]
    else:
        snippet = context
    print(f"[DEBUG] {model_name} sees: {snippet}")


def main():
    candidate_model = "anthropic/claude-sonnet-4"  # google/gemma-3n-e4b-it:free
    judge_model = "anthropic/claude-sonnet-4"
    starting_point = get_starting_point()
    print(f"Starting scenario: {starting_point}\n")

    # Initialize conversation with candidate
    candidate_context = candidate_prompt.format(starting_point=starting_point)
    candidate_response = get_candidate_response(
        model=candidate_model, context=candidate_context
    )

    print(f"Candidate's opening: {candidate_response}\n")

    # Initialize judge context
    judge_context = f"{judge_prompt}\n\nCandidate: {candidate_response}"

    turn_count = 0
    max_turns = 15  # Safety limit

    while turn_count < max_turns:
        turn_count += 1
        print(f"--- Turn {turn_count} ---")

        # Debug: Show judge context length
        print(f"[DEBUG] Judge context length: {len(judge_context)} chars")
        _debug_show_context(judge_context, "Judge")

        # Get judge response
        judge_response = get_judge_response(model=judge_model, context=judge_context)

        # Check if conversation ended
        if isinstance(judge_response, dict) and judge_response.get("ended"):
            print(f"\nConversation ended after {turn_count} turns")
            print(f"Reason: {judge_response['reason']}")
            print(f"Final impression: {judge_response['final_impression']}")
            break

        print(f"Judge: {format_message_for_candidate(judge_response)}")

        # Get candidate response to judge
        candidate_context += f"\n\nThem: {format_message_for_candidate(judge_response)}"

        # Debug: Show candidate context length
        print(f"[DEBUG] Candidate context length: {len(candidate_context)} chars")
        _debug_show_context(candidate_context, "Candidate")

        candidate_response = get_candidate_response(
            model=candidate_model, context=candidate_context
        )

        print(f"Candidate: {candidate_response}\n")

        # Update contexts for next turn
        candidate_context += f"\n\nYou: {candidate_response}"
        # Judge context should preserve the full judge response (including notes) then add candidate response
        judge_context += (
            f"\n\nJudge: {judge_response}\n\nCandidate: {candidate_response}"
        )

    if turn_count >= max_turns:
        print(f"\nConversation reached maximum turns ({max_turns})")


if __name__ == "__main__":
    main()
