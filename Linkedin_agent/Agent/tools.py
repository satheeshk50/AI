from langchain_community.tools import TavilySearchResults
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode


tavily_search = TavilySearchResults(max_results=5)

@tool
def search(query: str) -> str:
    """
    Search the web for information.
    Args:
        query (str): The search query.
    Returns:
        str: A formatted string with search results.
    """
    try:
        results = tavily_search.invoke(query)
        if results:
            formatted_results = []
            for result in results:
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    content = result.get('content', result.get('snippet', 'No content'))
                    url = result.get('url', '')
                    formatted_results.append(f"**{title}**\n{content}\nURL: {url}\n")
                else:
                    formatted_results.append(str(result))
            return "\n".join(formatted_results)
        else:
            return "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

# Set up tools
tools = [search]
tools_node = ToolNode(tools)