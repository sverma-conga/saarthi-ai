"""
Main Orchestrator Agent — The brain of SAARTHI AI.

Implements the Observe → Think → Act → Observe loop.
Returns ONLY the next action, not a full execution plan.
"""

import logging

from openai import AsyncOpenAI

from agents.intent_classifier import classify_intent
from agents.planner import plan_task
from agents.executor import execute_step
from agents.recovery import recover_from_error
from agents.guide_agent import generate_guide
from memory.session_store import session_store
from rag.hybrid_search import hybrid_search
from rag.retriever import retrieve_context
from schemas.request import OrchestratorRequest
from schemas.response import (
    OrchestratorResponse,
    ActionDetail,
    GuideStep,
    TaskState,
)

logger = logging.getLogger(__name__)


async def process_request(
    request: OrchestratorRequest,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> OrchestratorResponse:
    """Main entry point: process a single request through the agentic loop.

    Flow:
    1. Classify intent
    2. Route to appropriate flow (action/guide/knowledge/navigation)
    3. For actions: plan → execute next step → return single action
    4. For errors: invoke recovery agent
    """

    # --- Restore or create session ---
    task_state_dict = request.task_state.model_dump() if request.task_state else None
    session = session_store.get_or_restore(request.session_id, task_state_dict)
    session.last_page = request.context.url

    # --- Handle error recovery from last action ---
    if request.error_from_last_action:
        return await _handle_error_recovery(request, session, client, model)

    # --- If we have a plan in progress and no error, advance to next step ---
    if session.pending_steps and not request.error_from_last_action:
        # Only mark step complete if the previous action was a real action (not a wait)
        prev_was_real_action = False
        if request.previous_actions:
            last_action = request.previous_actions[-1] if request.previous_actions else {}
            prev_was_real_action = last_action.get("type") not in ("wait", None)

        if prev_was_real_action or session.completed_steps:
            session.complete_current_step()

        if session.is_task_complete():
            task_state = session.to_dict()
            session_store.remove(request.session_id)
            return OrchestratorResponse(
                session_id=request.session_id,
                message=f"Done! I've completed: {session.goal}",
                mode="action",
                done=True,
                task_state=TaskState(**task_state),
            )

        # Execute the next pending step
        return await _execute_next_step(request, session, client, model)

    # --- Fresh request: classify intent ---
    intent_result = await classify_intent(request.user_input, client, model)
    intent = intent_result["intent"]

    # --- Retrieve RAG context ---
    rag_context = _get_rag_context(request.user_input)

    # --- Route by intent ---
    if intent == "KNOWLEDGE":
        return await _handle_knowledge(request, rag_context, client, model)

    if intent in ("GUIDE", ) or request.mode == "guide":
        return await _handle_guide(request, rag_context, client, model)

    if intent in ("ACTION", "NAVIGATION"):
        return await _handle_action(request, session, rag_context, client, model)

    # UNKNOWN intent
    return OrchestratorResponse(
        session_id=request.session_id,
        message="I'm not sure what you'd like me to do. Could you rephrase your request?",
        mode="action",
        done=True,
    )


def _get_rag_context(query: str) -> str:
    """Try hybrid search first, fall back to vector-only."""
    try:
        context = hybrid_search(query, k=3)
        if context:
            return context
    except Exception:
        pass

    try:
        return retrieve_context(query, k=3)
    except Exception:
        return ""


async def _handle_knowledge(
    request: OrchestratorRequest,
    rag_context: str,
    client: AsyncOpenAI,
    model: str,
) -> OrchestratorResponse:
    """Answer a knowledge question using RAG context."""
    if rag_context:
        prompt = f"""Using the following knowledge base context, answer the user's question concisely.

## Knowledge Context:
{rag_context}

## Question:
{request.user_input}

Provide a clear, helpful answer. If the context doesn't contain the answer, say so."""
    else:
        prompt = f"""Answer the following question about Conga CLM (Contract Lifecycle Management) to the best of your knowledge. Be concise.

## Question:
{request.user_input}"""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are SAARTHI AI, an expert on Conga CLM."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=500,
    )

    answer = response.choices[0].message.content

    return OrchestratorResponse(
        session_id=request.session_id,
        message=answer,
        mode="knowledge",
        done=True,
    )


async def _handle_guide(
    request: OrchestratorRequest,
    rag_context: str,
    client: AsyncOpenAI,
    model: str,
) -> OrchestratorResponse:
    """Generate step-by-step guide."""
    elements = [el.model_dump() for el in request.context.interactive_elements]
    page_context = {
        "url": request.context.url,
        "page_title": request.context.page_title,
        "visible_text_summary": request.context.visible_text_summary,
    }

    guide_result = await generate_guide(
        request.user_input, elements, page_context, rag_context, client, model
    )

    guide_steps = [
        GuideStep(**step) for step in guide_result.get("guide_steps", [])
    ]

    return OrchestratorResponse(
        session_id=request.session_id,
        message=guide_result.get("message", "Here are the steps:"),
        mode="guide",
        guide_steps=guide_steps,
        done=guide_result.get("done", True),
    )


async def _handle_action(
    request: OrchestratorRequest,
    session,
    rag_context: str,
    client: AsyncOpenAI,
    model: str,
) -> OrchestratorResponse:
    """Plan a task and execute the first step."""

    # 1. Generate plan
    plan = await plan_task(request.user_input, rag_context, client, model)

    # 2. Store plan in session
    session.set_plan(plan.get("goal", request.user_input), plan.get("steps", []))

    # 3. Execute the first step
    return await _execute_next_step(request, session, client, model)


async def _execute_next_step(
    request: OrchestratorRequest,
    session,
    client: AsyncOpenAI,
    model: str,
) -> OrchestratorResponse:
    """Execute the next pending step in the session plan."""
    current_step = session.get_current_step()
    if not current_step:
        task_state = session.to_dict()
        session_store.remove(request.session_id)
        return OrchestratorResponse(
            session_id=request.session_id,
            message="All steps completed!",
            mode="action",
            done=True,
            task_state=TaskState(**task_state),
        )

    elements = [el.model_dump() for el in request.context.interactive_elements]
    page_context = {
        "url": request.context.url,
        "page_title": request.context.page_title,
        "visible_text_summary": request.context.visible_text_summary,
    }

    exec_result = await execute_step(current_step, elements, page_context, client, model)

    action_data = exec_result.get("action", {})
    next_action = ActionDetail(**action_data) if action_data else None

    # Determine progress
    total = len(session.planned_steps)
    completed = len(session.completed_steps)
    progress = f" (step {completed + 1}/{total})" if total > 1 else ""

    return OrchestratorResponse(
        session_id=request.session_id,
        message=exec_result.get("message", f"Executing: {current_step}") + progress,
        mode="action",
        next_action=next_action,
        done=False,
        follow_up=f"Waiting for result of: {current_step}",
        task_state=TaskState(**session.to_dict()),
    )


async def _handle_error_recovery(
    request: OrchestratorRequest,
    session,
    client: AsyncOpenAI,
    model: str,
) -> OrchestratorResponse:
    """Handle a failed action via the recovery agent."""
    session.increment_retry()

    elements = [el.model_dump() for el in request.context.interactive_elements]
    page_context = {
        "url": request.context.url,
        "page_title": request.context.page_title,
        "visible_text_summary": request.context.visible_text_summary,
    }

    # Get the failed action from previous_actions
    failed_action = request.previous_actions[-1] if request.previous_actions else {}

    recovery = await recover_from_error(
        error=request.error_from_last_action,
        failed_action=failed_action,
        interactive_elements=elements,
        page_context=page_context,
        retry_count=session.retry_count,
        client=client,
        model=model,
    )

    if recovery["strategy"] == "ask_user":
        return OrchestratorResponse(
            session_id=request.session_id,
            message=recovery["message"],
            mode="action",
            done=True,
            task_state=TaskState(**session.to_dict()),
        )

    action_data = recovery.get("action")
    next_action = ActionDetail(**action_data) if action_data else None

    return OrchestratorResponse(
        session_id=request.session_id,
        message=recovery["message"],
        mode="action",
        next_action=next_action,
        done=False,
        follow_up=f"Recovery: {recovery['strategy']}",
        task_state=TaskState(**session.to_dict()),
    )
