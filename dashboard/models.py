"""
dashboard/models.py — Persistent data models for the Financial Agent.
Stores research query histories and report summaries (Phase 7).
"""
from django.db import models


class ResearchSession(models.Model):
    """Stores past research runs and synthesised reports."""
    ticker       = models.CharField(max_length=10, db_index=True)
    query        = models.TextField()
    summary      = models.TextField()
    indicators   = models.JSONField(default=dict, blank=True)
    fundamentals = models.JSONField(default=dict, blank=True)
    news         = models.JSONField(default=list, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticker} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def to_dict(self):
        """Serialize session for history API."""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "query": self.query,
            "summary": self.summary,
            "indicators": self.indicators,
            "fundamentals": self.fundamentals,
            "news": self.news,
            "created_at": self.created_at.strftime("%b %d, %Y %H:%M"),
        }
