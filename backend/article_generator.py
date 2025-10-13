# [backend/article_generator.py] 파일

import os
import sys
from typing import TypedDict, Annotated, Sequence
import operator

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import Tool
from langchain.tools.retriever import create_retriever_tool
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage, FunctionMessage

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

# Local imports
from backend.rag_processor import RAGProcessor

# Add the parent directory to the system path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 2. Define Agent (Nodes and Edges) ---
class Agent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.graph = self._build_graph(tools)

    def _build_graph(self, tools):
        graph = StateGraph(AgentState)
        graph.add_node("call_model", self.call_model)
        tool_node = ToolNode(tools)
        graph.add_node("call_tool", tool_node)
        graph.add_conditional_edges(
            "call_model",
            tools_condition,
            {
                "tools": "call_tool",
                END: END,
            }
        )
        graph.add_edge("call_tool", "call_model")
        graph.set_entry_point("call_model")
        return graph.compile()

    def call_model(self, state: AgentState):
        response = self.llm.invoke(state['messages'])
        return {'messages': [response]}

# --- Main Class ---
class ArticleGenerator:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        # Bind tools to the LLM
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=self.api_key)
        self.agent = self._create_agent()

    def _create_agent(self):
        """Creates the LangGraph agent."""
        
        # 1. Create Tools
        rag_processor = RAGProcessor()
        vector_store = rag_processor.load_vector_store()
        retriever = vector_store.as_retriever()
        
        retriever_tool = create_retriever_tool(
            retriever,
            "health_info_search",
            "Searches and returns relevant health information from a database of articles. Use this for any questions about health topics, conditions, treatments, etc."
        )
        
        def _article_generator_func(input_str: str) -> str:
            return "Article generation is a complex process that should be initiated from the admin panel, not through this agent."

        article_gen_tool = Tool(
            name="article_generator",
            func=_article_generator_func,
            description="Use this tool only when explicitly asked to generate a completely new article from scratch."
        )

        tools = [retriever_tool, article_gen_tool]
        self.llm = self.llm.bind_tools(tools)

        # 2. Create Agent
        agent = Agent(self.llm, tools)
        return agent.graph

    def run_agent(self, user_input: str, chat_history: list = []):
        """Runs the agent with the given user input and chat history."""
        
        messages = []
        # Convert chat history to BaseMessages
        for role, content in chat_history:
            if role == 'user':
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "ai", "content": content})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})

        # The prompt is now implicitly handled by the agent's structure and the bound LLM
        response = self.agent.invoke({"messages": messages})
        
        # Extract the last AI message as the final output
        return response['messages'][-1].content

    def generate_new_article(self, title: str, content: str) -> str:
        """
        Generates a new article based on the original title and content,
        targeting a 50-70 year old audience.
        """
        prompt_template_str = """
        당신은 50대-70대 독자를 위한 건강 전문 작가입니다.
        아래 주어진 원본 기사의 제목과 내용을 바탕으로, 독자들이 이해하기 쉽고 실용적인 정보를 얻을 수 있도록 새로운 건강 기사를 작성해 주세요.

        - **목표**: 원본 기사의 핵심 정보를 유지하되, 더 친절하고 부드러운 어조로 설명합니다.
        - **형식**: 독자가 읽기 편하도록 문단을 나누고, 중요한 부분은 강조해 주세요.
        - **내용**: 전문 용어는 쉽게 풀어서 설명하고, 일상 생활에서 실천할 수 있는 팁을 포함하면 좋습니다.
        - **분량**: 원본 기사와 비슷하거나 약간 더 상세하게 작성해 주세요.
        - **출력**: 제목과 내용을 포함한 완결된 기사 형식으로 작성해 주세요. (예: "새로운 제목\n\n첫 번째 문단...")

        ---
        **원본 기사 제목**: {title}
        ---
        **원본 기사 내용**:
        {content}
        ---

        이제 위의 내용을 바탕으로 새로운 기사를 작성해 주세요.
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template_str)
        output_parser = StrOutputParser()
        
        # Use a non-tool-bound LLM for this simple chain
        article_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=self.api_key)
        chain: Runnable = prompt | article_llm | output_parser
        
        try:
            new_article = chain.invoke({"title": title, "content": content})
            return new_article.strip()
        except Exception as e:
            print(f"New article generation with LangChain failed: {e}")
            # Return a user-friendly error message in Korean
            return "죄송합니다, AI 기사 생성 중 예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def generate_short_script(self, content):
        """Generates a short video script from the article content using LangChain."""
        prompt_template_str = """
        당신은 50-70대 시청자를 위한 건강 정보 영상의 전문 작가입니다.
        주어진 기사 내용을 바탕으로, 친절하고 이해하기 쉬운 톤으로 영상 대본을 작성해 주세요.
        대본은 약 150-200 단어 길이로 요약되어야 합니다.
        장면 전환이나 시간 표시 없이, 오직 나레이션 대본만 작성해 주세요.
        **대본은 반드시 한국어로 작성해야 합니다.**

        기사 내용:
        ---
        {article_content}
        ---

        이제 영상 대본을 작성해 주세요.
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template_str)
        output_parser = StrOutputParser()
        
        # Use a non-tool-bound LLM for this simple chain
        script_llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=self.api_key)
        chain: Runnable = prompt | script_llm | output_parser
        
        try:
            script = chain.invoke({"article_content": content})
            return script.strip()
        except Exception as e:
            print(f"Script generation with LangChain failed: {e}")
            return "스크립트 생성에 실패했습니다."
