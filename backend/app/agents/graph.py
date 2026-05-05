import logging
from typing import Optional, Any

from deepagents import create_deep_agent

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
    "You are a helpful personal assistant and routing supervisor. "
    "You converse with the user and delegate tasks to domain experts using the task tool when needed. "
    "If the user is just chatting or asking general questions, answer directly. "
    "If the request requires specific actions or knowledge, delegate to the correct expert. "
    "Always summarize the expert's findings to the user."
)

PRODUCTS_AGENT_PROMPT = (
    "You are a product catalog specialist. "
    "You have access to tools to list products and get specific product details. "
    "Help the user find the right product and provide accurate price information. "
    "Always clarify product names and prices."
)

SALES_AGENT_PROMPT = (
    "You are a sales performance analyst. "
    "You can list transaction history and provide sales summaries. "
    "Help the user understand sales trends and financial metrics. "
    "Provide clear summaries of revenue and sales volume."
)

# --- Metadados dos Especialistas (Dynamic Tags) ---
EXPERTS_METADATA = {
    "products": {
        "description": "Consult product catalog, inventory, and prices. Use for finding items to buy.",
        "prompt": PRODUCTS_AGENT_PROMPT
    },
    "sales": {
        "description": "Analyze sales history, revenue, and transaction metrics.",
        "prompt": SALES_AGENT_PROMPT
    }
}

async def build_main_graph(checkpointer=None, mcp_server: Any = None):
    """Constrói o DeepAgent usando a biblioteca deepagents."""
    from ..tools.mcp_client import mcp_discovery
    logger.info("Construindo grafo usando deepagents...")
    
    subagents = []
    
    # 1. Native Agents (HITL maintained via interrupt_on)
    subagents.append({
        "name": "calendar",
        "description": "Manage calendar, schedule events, and check time availability.",
        "system_prompt": CALENDAR_AGENT_PROMPT,
        "tools": [create_calendar_event, get_available_time_slots],
        "interrupt_on": {"create_calendar_event": {"allowed_decisions": ["approve", "reject"]}},
    })
    
    subagents.append({
        "name": "email",
        "description": "Send emails and notifications.",
        "system_prompt": EMAIL_AGENT_PROMPT,
        "tools": [send_email],
        "interrupt_on": {"send_email": {"allowed_decisions": ["approve", "reject"]}},
    })
    
    # 2. Dynamic MCP Agents
    for tag, meta in EXPERTS_METADATA.items():
        tools = await mcp_discovery.get_tools(tag=tag, mcp_server=mcp_server)
        if tools:
            subagents.append({
                "name": tag,
                "description": meta["description"],
                "system_prompt": meta["prompt"],
                "tools": tools,
            })
            logger.info(f"Sub-agente '{tag}' adicionado com {len(tools)} ferramentas.")
    
    # Criamos o agente principal
    agent = create_deep_agent(
        model=get_llm(),
        system_prompt=SUPERVISOR_PROMPT,
        subagents=subagents,
        checkpointer=checkpointer,
        name="supervisor"
    )
    
    return agent
