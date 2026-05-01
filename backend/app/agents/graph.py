import logging
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphInterrupt

from ..core.llm import get_llm
from ..tools.tools import create_calendar_event, get_available_time_slots, send_email

logger = logging.getLogger(__name__)

# --- Prompts ---

CALENDAR_AGENT_PROMPT = (
    "You are a calendar scheduling assistant. "
    "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
    "into proper ISO datetime formats. "
    "Use get_available_time_slots to check availability when needed. "
    "If there is no suitable time slot, stop and confirm "
    "unavailability in your response. "
    "Use create_calendar_event to schedule events. "
    "Always confirm what was scheduled in your final response."
)

EMAIL_AGENT_PROMPT = (
    "You are an email assistant. "
    "Compose professional emails based on natural language requests. "
    "Extract recipient information and craft appropriate subject lines and body text. "
    "Use send_email to send the message. "
    "Always confirm what was sent in your final response."
)

SUPERVISOR_PROMPT = (
    "You are a helpful personal assistant. "
    "You can schedule calendar events, send emails, consult the product catalog, and analyze sales. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

PRODUCTS_AGENT_PROMPT = (
    "You are a product catalog specialist. "
    "You have access to tools to list products and get specific product details. "
    "Help the user find the right product and provide accurate price information. "
    "Always clarify product names and prices to the user."
)

SALES_AGENT_PROMPT = (
    "You are a sales performance analyst. "
    "You can list transaction history and provide sales summaries. "
    "Help the user understand sales trends and financial metrics. "
    "Provide clear summaries of revenue and sales volume."
)

# --- Agentes Estáticos (Shared) ---

_calendar_agent = None
_email_agent = None
_products_agent = None
_sales_agent = None


def create_static_agents(checkpointer=None):
    """Fábrica para criar os sub-agentes que não dependem do MCP."""
    llm = get_llm()

    calendar_agent = create_agent(
        llm,
        tools=[create_calendar_event, get_available_time_slots],
        system_prompt=CALENDAR_AGENT_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"create_calendar_event": True},
                description_prefix="Calendar event pending approval",
            ),
        ],
        checkpointer=checkpointer,
    )

    email_agent = create_agent(
        llm,
        tools=[send_email],
        system_prompt=EMAIL_AGENT_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "send_email": {"allowed_decisions": ["approve", "reject"]},
                },
                description_prefix="Outbound email pending approval",
            ),
        ],
        checkpointer=checkpointer,
    )

    return calendar_agent, email_agent


def initialize_global_agents(checkpointer=None):
    """Inicializa os agentes estáticos no boot."""
    global _calendar_agent, _email_agent
    _calendar_agent, _email_agent = create_static_agents(checkpointer=checkpointer)
    return _calendar_agent, _email_agent


# --- Ferramentas de Orquestração ---


@tool
async def schedule_event(request: str, config: RunnableConfig) -> str:
    """Schedule calendar events using natural language.
    Use this when the user wants to create, modify, or check calendar appointments.
    """
    if _calendar_agent is None:
        return "Erro: Agente de calendário não inicializado."
    try:
        result = await _calendar_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config, version="v2"
        )
        return result.messages[-1].content
    except GraphInterrupt as e:
        raise e


@tool
async def manage_email(request: str, config: RunnableConfig) -> str:
    """Send emails using natural language.
    Use this when the user wants to send notifications, reminders,
    or any email communication.
    """
    if _email_agent is None:
        return "Erro: Agente de e-mail não inicializado."
    try:
        result = await _email_agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config, version="v2"
        )
        return result.messages[-1].content
    except GraphInterrupt as e:
        raise e


async def ensure_products_agent(config: RunnableConfig):
    """Garante que o agente de produtos esteja inicializado."""
    global _products_agent
    if _products_agent is None:
        from ..tools.mcp_client import mcp_discovery
        llm = get_llm()
        # Busca ferramentas dinamicamente por tag
        tools = await mcp_discovery.get_tools(tag="products")
        logger.info(f"Agente de Produtos inicializado com {len(tools)} ferramentas MCP.")
        
        _products_agent = create_agent(
            llm,
            tools=tools,
            system_prompt=PRODUCTS_AGENT_PROMPT,
            checkpointer=config.get("configurable", {}).get("checkpointer")
        )
    return _products_agent


async def ensure_sales_agent(config: RunnableConfig):
    """Garante que o agente de vendas esteja inicializado."""
    global _sales_agent
    if _sales_agent is None:
        from ..tools.mcp_client import mcp_discovery
        llm = get_llm()
        # Busca ferramentas dinamicamente por tag
        tools = await mcp_discovery.get_tools(tag="sales")
        logger.info(f"Agente de Vendas inicializado com {len(tools)} ferramentas MCP.")
        
        _sales_agent = create_agent(
            llm,
            tools=tools,
            system_prompt=SALES_AGENT_PROMPT,
            checkpointer=config.get("configurable", {}).get("checkpointer")
        )
    return _sales_agent


@tool
async def consult_products(request: str, config: RunnableConfig) -> str:
    """Consult the product catalog.
    Use this when the user asks about available products, prices, or inventory.
    """
    logger.info(f"Supervisor delegando para Agente de Produtos: {request}")
    agent = await ensure_products_agent(config)
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content
    except GraphInterrupt as e:
        raise e


@tool
async def analyze_sales(request: str, config: RunnableConfig) -> str:
    """Analyze sales history and summaries.
    Use this when the user asks about sales performance, revenue, or transaction history.
    """
    agent = await ensure_sales_agent(config)
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request)]}, config=config
        )
        return result["messages"][-1].content
    except GraphInterrupt as e:
        raise e
