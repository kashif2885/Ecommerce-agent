"""
RAG tool factory – returns a @tool that searches the ChromaDB vectorstore.
The description is intentionally detailed so the ReAct LLM knows to call
this for any company/policy/FAQ question, without an external classifier.
"""
from langchain_core.tools import tool


def make_rag_tool(vectorstore):
    """Return a LangChain tool that searches the knowledge-base vectorstore."""

    @tool
    def search_knowledge_base(query: str) -> str:
        """Search the company knowledge base and return relevant information.

        Use this tool when the user asks about ANY of the following:
          - Company background, history, or general information
          - Services offered and how to access them
          - Rewards or loyalty programs (e.g. eligibility, earning, redeeming points)
          - Policies: fees, cancellations, refunds, terms and conditions
          - FAQs and how-to questions about company processes
          - Anything the user asks about 'your company', 'your services',
            or 'how does X work' that isn't a product or appointment

        Always call this tool instead of guessing when the question is about
        company information – never fabricate policies or program details.

        Args:
            query: A natural-language question or search phrase describing
                   what the user wants to know (e.g. 'how do I earn reward
                   points?', 'what is the cancellation policy?',
                   'tell me about the Adventurer Rewards program').

        Returns:
            Relevant text passages retrieved from the knowledge base,
            formatted as numbered sources.  Use this content verbatim
            or summarise it accurately in your response.
        """
        try:
            docs = vectorstore.similarity_search(query, k=4)
            if not docs:
                return "No relevant information found in the knowledge base."
            parts = [f"[Source {i + 1}]\n{doc.page_content}" for i, doc in enumerate(docs)]
            return "\n\n---\n\n".join(parts)
        except Exception as exc:
            return f"Error searching knowledge base: {exc}"

    return search_knowledge_base
