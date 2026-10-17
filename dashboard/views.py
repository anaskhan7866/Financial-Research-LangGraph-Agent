"""
dashboard/views.py — View functions for the Financial Research Agent UI.
Integrates LangGraph multi-agent supervisor with real-time streaming (Phase 6 & 7).
"""
import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from agent.graph import run_agent, agent_app
from agent.state import create_initial_state
from agent.nodes import check_fallback_data
from agent.config import logger
from dashboard.models import ResearchSession


def index(request):
    """Main dashboard page."""
    return render(request, "dashboard/index.html")


def _format_final_result(final_state: dict, query: str, ticker: str) -> dict:
    """Format research result dictionary with rate limit & fallback metadata."""
    is_fb = check_fallback_data(final_state)
    return {
        "ticker": final_state.get("ticker", ticker or "AAPL"),
        "query": final_state.get("query", query),
        "steps": final_state.get("steps", []),
        "fundamentals": final_state.get("fundamentals", {}),
        "indicators": final_state.get("indicators", {}),
        "news": final_state.get("news", []),
        "summary": final_state.get("final_answer", "No summary generated."),
        "is_fallback": is_fb,
        "warning": (
            "⚠️ Alpha Vantage daily free limit reached. Displaying cached/modeled fallback data to keep your analysis uninterrupted."
            if is_fb else None
        ),
    }


def _stream_agent_execution(query: str, ticker: str):
    """Yield Server-Sent Events (SSE) as LangGraph nodes execute in real time."""
    initial_state = create_initial_state(query=query, ticker=ticker)
    seen_steps = 0
    final_state = dict(initial_state)

    try:
        for chunk in agent_app.stream(initial_state):
            node_name = list(chunk.keys())[0]
            for k, v in chunk[node_name].items():
                if k == "messages":
                    final_state["messages"] = final_state.get("messages", []) + v
                else:
                    final_state[k] = v

            current_steps = final_state.get("steps", [])
            while seen_steps < len(current_steps):
                step = current_steps[seen_steps]
                seen_steps += 1
                yield f"data: {json.dumps({'type': 'step', 'step': step})}\n\n"

        result = _format_final_result(final_state, query, ticker)
        _persist_session(result["ticker"], query, result)
        yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"
    except Exception as e:
        logger.error(f"Error in streaming graph: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@csrf_exempt
@require_POST
def analyze(request):
    """
    Run LangGraph Agent with real-time SSE streaming or standard JSON response.
    Saves completed run to ResearchSession history.
    """
    try:
        body = json.loads(request.body.decode("utf-8") if request.body else "{}")
        if not isinstance(body, dict):
            return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

        query = str(body.get("query", "")).strip()
        ticker = str(body.get("ticker", "AAPL")).strip().upper() or "AAPL"

        if not query:
            return JsonResponse({"error": "Query cannot be empty."}, status=400)

        # Stream real-time execution steps if requested by frontend
        accept_header = request.headers.get("Accept", "")
        if "text/event-stream" in accept_header or request.GET.get("stream") == "1":
            response = StreamingHttpResponse(
                _stream_agent_execution(query, ticker),
                content_type="text/event-stream"
            )
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response

        # Standard non-streaming JSON response for backward compatibility & tests
        response = run_agent(query=query, ticker=ticker)
        _persist_session(ticker, query, response)
        return JsonResponse(response)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
    except Exception as e:
        logger.error(f"Error in analyze view: {e}")
        return JsonResponse({"error": f"Analysis failed: {str(e)}"}, status=500)


def history(request):
    """Returns recent research sessions from SQLite database."""
    try:
        sessions = ResearchSession.objects.all()[:15]
        return JsonResponse({"history": [s.to_dict() for s in sessions]})
    except Exception as e:
        logger.warning(f"Failed to retrieve history: {e}")
        return JsonResponse({"history": []})


def _persist_session(ticker: str, query: str, data: dict):
    """Save completed research session to database safely."""
    try:
        ResearchSession.objects.create(
            ticker=ticker,
            query=query,
            summary=data.get("summary", ""),
            indicators=data.get("indicators", {}),
            fundamentals=data.get("fundamentals", {}),
            news=data.get("news", []),
        )
        old_ids = ResearchSession.objects.values_list("id", flat=True)[50:]
        if old_ids:
            ResearchSession.objects.filter(id__in=list(old_ids)).delete()
    except Exception as err:
        logger.warning(f"Could not save research session: {err}")
