import os
from openai import OpenAI
from dotenv import load_dotenv

from app.prompts.templates import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_answer(question: str, context_chunks: list[dict]) -> str:
    """
    Generate an answer using OpenAI LLM.

    Args:
        question: User's question
        context_chunks: Retrieved chunks from RAG

    Returns:
        Generated answer string
    """

    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        source = chunk["metadata"].get("title", "Unknown")
        content = chunk["content"]
        context_parts.append(f"[Source: {source}]\n{content}")

    context = "\n\n".join(context_parts)

    # Build the prompt
    user_prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=question
    )

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Fast and cheap
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content
