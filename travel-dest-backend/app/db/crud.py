"""Small CRUD helpers for auth, history, and tool call persistence."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import AgentRun, ToolCall, User


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return one user by email if it exists."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Return one user by id if it exists."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password_hash: str) -> User:
    """Create and persist a new user."""
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_agent_run(db: Session, user_id: UUID, user_query: str) -> AgentRun:
    """Create a new agent run row before orchestration starts."""
    agent_run = AgentRun(user_id=user_id, user_query=user_query)
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)
    return agent_run


def update_agent_run_result(
    db: Session,
    agent_run: AgentRun,
    final_answer: str,
    total_tokens: int,
    estimated_cost: float,
) -> AgentRun:
    """Store the final answer and usage metrics for one run."""
    agent_run.final_answer = final_answer
    agent_run.total_tokens = total_tokens
    agent_run.estimated_cost = estimated_cost
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)
    return agent_run


def create_tool_call(
    db: Session,
    agent_run_id: UUID,
    tool_name: str,
    tool_input: dict,
    tool_output: dict,
    status: str,
    latency_ms: int,
    error_message: str | None = None,
) -> ToolCall:
    """Persist one tool execution result."""
    tool_call = ToolCall(
        agent_run_id=agent_run_id,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        status=status,
        latency_ms=latency_ms,
        error_message=error_message,
    )
    db.add(tool_call)
    db.commit()
    db.refresh(tool_call)
    return tool_call


def list_agent_runs_for_user(db: Session, user_id: UUID) -> list[AgentRun]:
    """Return recent agent runs for one user."""
    return (
        db.query(AgentRun)
        .filter(AgentRun.user_id == user_id)
        .order_by(AgentRun.created_at.desc())
        .all()
    )

