from models import PhysicsRAGState
from langgraph.graph import StateGraph, END
from semantic_search import retrieve_chunks
from chunks_logics import build_context
from openai import OpenAI


client = OpenAI()


def classify_question(state):
    response = (

        client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {

                    "role": "system",

                    "content": """
You are a physics question classifier.

Classify the question into ONE category only.

Categories:

- theory
- derivation
- numerical
- comparison

Return ONLY the category name.
"""
                },

                {

                    "role": "user",

                    "content":
                        state.question
                }
            ],

            temperature=0
        )
    )

    query_type = (
        response
        .choices[0]
        .message.content
        .strip()
        .lower()
    )
    state.query_type = query_type
    return state

def route_by_query_type(state):
    return state.query_type

def rewrite_query(state):
    state.rewritten_query = f"CBSE Physics "f"{state.query_type} "f"{ state.question}"
    return state

def retrieval_node(state):
    chunks = retrieve_chunks(state.rewritten_query, top_k=5)
    if not chunks:
        state.no_context_found = True
        return state
    state.retrieved_chunks = chunks
    return state

def theory_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state
    
    context = build_context(state.retrieved_chunks)
    state.final_prompt = f"""
You are a strict CBSE Physics tutor.

Answer ONLY using the provided context.

IMPORTANT RULES:

- Do NOT use outside knowledge.
- Do NOT guess.
- Do NOT fabricate information.
- If answer is not present in context,
  reply exactly:

"No relevant information found in the knowledge base."

Generate a 10-mark theory answer.

Include:
- introduction
- explanation
- important points
- conclusion

IMPORTANT FORMATTING RULES:

1. NEVER write equations like:
[ equation ]

2. ALWAYS use proper LaTeX blocks:

$$
equation
$$

3. Use inline math with:
$equation$

4. Every physics equation must be in LaTeX.

5. Do NOT use escaped brackets like:
\( equation \)

6. Use clean readable mathematical formatting.

Generate a FULL-MARKS 10-mark answer.

Rules:

- use board exam style
- concise but complete
- use headings
- include derivation steps
- include important points
- avoid unnecessary advanced concepts
- stay strictly within CBSE syllabus

Use ONLY the provided sources.

When using information,
mention source references.

Example:

(Source:
HC Verma Vol 1, Page 233)

Context:
{context}

Question:
{state.question}
"""
    return state

def derivation_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state
    
    context = build_context(state.retrieved_chunks)
    state.final_prompt = f"""
You are a strict CBSE Physics tutor.

Answer ONLY using the provided context.

IMPORTANT RULES:

- Do NOT use outside knowledge.
- Do NOT guess.
- Do NOT fabricate information.
- If answer is not present in context,
  reply exactly:

"No relevant information found in the knowledge base."

Generate a derivation answer.

Include:
- introduction
- formulas
- derivation steps
- final formula
- conclusion

IMPORTANT FORMATTING RULES:

1. NEVER write equations like:
[ equation ]

2. ALWAYS use proper LaTeX blocks:

$$
equation
$$

3. Use inline math with:
$equation$

4. Every physics equation must be in LaTeX.

5. Do NOT use escaped brackets like:
\( equation \)

6. Use clean readable mathematical formatting.

Generate a FULL-MARKS 10-mark answer.

Rules:

- use board exam style
- concise but complete
- use headings
- include derivation steps
- include important points
- avoid unnecessary advanced concepts
- stay strictly within CBSE syllabus

Use ONLY the provided sources.

When using information,
mention source references.

Example:

(Source:
HC Verma Vol 1, Page 233)

Context:
{context}

Question:
{state.question}
"""
    return state

def numerical_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state
    context = build_context(state.retrieved_chunks)
    state.final_prompt = f"""
You are a strict CBSE Physics tutor.

Answer ONLY using the provided context.

IMPORTANT RULES:

- Do NOT use outside knowledge.
- Do NOT guess.
- Do NOT fabricate information.
- If answer is not present in context,
  reply exactly:

"No relevant information found in the knowledge base."

Solve step-by-step.

Format:

1. Given
2. Formula Used
3. Substitution
4. Calculation
5. Final Answer with Units

- Use Greek symbols properly
- Use proper mathematical notation
- Use LaTeX for all formulas
- Never write raw escape characters
- Put every major equation in block math format

IMPORTANT FORMATTING RULES:

1. NEVER write equations like:
[ equation ]

2. ALWAYS use proper LaTeX blocks:

$$
equation
$$

3. Use inline math with:
$equation$

4. Every physics equation must be in LaTeX.

5. Do NOT use escaped brackets like:
\( equation \)

6. Use clean readable mathematical formatting.

Generate a FULL-MARKS 10-mark answer.

Rules:

- use board exam style
- concise but complete
- use headings
- include derivation steps
- include important points
- avoid unnecessary advanced concepts
- stay strictly within CBSE syllabus

Use ONLY the provided sources.

When using information,
mention source references.

Example:

(Source:
HC Verma Vol 1, Page 233)

Context:
{context}

Question:
{state.question}
"""
    return state

def comparison_generator(state):
    if state.no_context_found:
        state.final_prompt = None
        return state
    context = build_context(state.retrieved_chunks)
    state.final_prompt = f"""
You are a strict CBSE Physics tutor.

Answer ONLY using the provided context.

IMPORTANT RULES:

- Do NOT use outside knowledge.
- Do NOT guess.
- Do NOT fabricate information.
- If answer is not present in context,
  reply exactly:

"No relevant information found in the knowledge base."    

Compare the concepts clearly.

Use:
- definitions
- differences table
- examples

IMPORTANT FORMATTING RULES:

1. NEVER write equations like:
[ equation ]

2. ALWAYS use proper LaTeX blocks:

$$
equation
$$

3. Use inline math with:
$equation$

4. Every physics equation must be in LaTeX.

5. Do NOT use escaped brackets like:
\( equation \)

6. Use clean readable mathematical formatting.

Generate a FULL-MARKS 10-mark answer.

Rules:

- use board exam style
- concise but complete
- use headings
- include derivation steps
- include important points
- avoid unnecessary advanced concepts
- stay strictly within CBSE syllabus

Use ONLY the provided sources.

When using information,
mention source references.

Example:

(Source:
HC Verma Vol 1, Page 233)

Context:
{context}

Question:
{state.question}
"""
    return state

def llm_node(state):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content":state.final_prompt
        }]
    )
    state.final_answer = (
        response
        .choices[0]
        .message.content
    )
    return state


graph = StateGraph(PhysicsRAGState)


graph.add_node("classifier",classify_question)

graph.add_node("rewrite",rewrite_query)

graph.add_node("retrieve",retrieval_node)

graph.add_node("theory",theory_generator)

graph.add_node("derivation",derivation_generator)

graph.add_node("numerical",numerical_generator)

graph.add_node("comparison",comparison_generator)

graph.add_node("llm",llm_node)


graph.set_entry_point("classifier")

graph.add_conditional_edges(
    "classifier",
    route_by_query_type,
    {
        "theory":
            "rewrite",
        "derivation":
            "rewrite",
        "numerical":
            "rewrite",
        "comparison":
            "rewrite"
    }
)

graph.add_edge("rewrite","retrieve")

graph.add_conditional_edges(
    "retrieve",
    route_by_query_type,
    {
        "theory":
            "theory",
        "derivation":
            "derivation",
        "numerical":
            "numerical",
        "comparison":
            "comparison"
    }
)

graph.add_edge("theory","llm")

graph.add_edge("derivation","llm")

graph.add_edge("numerical","llm")

graph.add_edge("comparison","llm")

graph.add_edge("llm",END)


app = graph.compile()


if __name__ == "__main__":
    png_data = app.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_data)