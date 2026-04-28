from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from llm import get_llm
from tools import create_calendar_event, get_available_time_slots, send_email

# --- Prompts ---

CALENDAR_AGENT_PROMPT = (
    "You are a calendar scheduling assistant. "
    "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
    "into proper ISO datetime formats. "
    "Use get_available_time_slots to check availability when needed. "
    "If there is no suitable time slot, stop and confirm unavailability in your response. "
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
    "You can schedule calendar events and send emails. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

# --- Agentes Estáticos (Shared) ---

_calendar_agent = None
_email_agent = None

def create_sub_agents():
    """Fábrica para criar os sub-agentes especialistas."""
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
    )

    email_agent = create_agent(
        llm,
        tools=[send_email],
        system_prompt=EMAIL_AGENT_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"send_email": True},
                description_prefix="Outbound email pending approval",
            ),
        ],
    )
    
    return calendar_agent, email_agent

def initialize_global_agents():
    """Inicializa os agentes globais para uso nas ferramentas de orquestração."""
    global _calendar_agent, _email_agent
    _calendar_agent, _email_agent = create_sub_agents()
    return _calendar_agent, _email_agent


# --- Ferramentas de Orquestração ---

@tool
async def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language.
    Use this when the user wants to create, modify, or check calendar appointments.
    """
    if _calendar_agent is None:
        return "Erro: Agente de calendário não inicializado."
    result = await _calendar_agent.ainvoke({"messages": [HumanMessage(content=request)]})
    return result["messages"][-1].content

@tool
async def manage_email(request: str) -> str:
    """Send emails using natural language.
    Use this when the user wants to send notifications, reminders, or any email communication.
    """
    if _email_agent is None:
        return "Erro: Agente de e-mail não inicializado."
    result = await _email_agent.ainvoke({"messages": [HumanMessage(content=request)]})
    return result["messages"][-1].content
