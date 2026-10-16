"""
dashboard/views.py — View functions for the Financial Research Agent UI.
Integrates LangGraph stateful agent with persistent SQLite history (Phase 6 & 7).
"""
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from agent.graph import run_agent
from agent.config import logger
from dashboard.models import ResearchSession


def index(request):
    """Main dashboard page."""
    return render(request, "dashboard/index.html")


@csrf_exempt
@require_POST
def analyze(request):
    """
    Receives JSON query and runs real LangGraph Financial Agent.
    Saves completed run to ResearchSession history.
    """
    try:
        if not request.body:
            return JsonResponse({"error": "Request body cannot be empty."}, status=400)

        body = json.loads(request.body)
        if not isinstance(body, dict):
            return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

        query  = str(body.get("query", "")).strip()
        ticker = str(body.get("ticker", "AAPL")).strip().upper() or "AAPL"

        if not query:
            return JsonResponse({"error": "Query cannot be empty."}, status=400)

        response = run_agent(query=query, ticker=ticker)

        # Persist session to database (Rule 7 error isolation)
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
        # Prune old records to keep database light (keep 50)
        old_ids = ResearchSession.objects.values_list("id", flat=True)[50:]
        if old_ids:
            ResearchSession.objects.filter(id__in=list(old_ids)).delete()
    except Exception as err:
        logger.warning(f"Could not save research session: {err}")
