"""Timeline event model for case timelines."""
from tortoise import fields
from tortoise.models import Model
from typing import Optional


class TimelineEvent(Model):
    """
    A legally significant event extracted from a document.
    
    Timeline events are extracted through a two-step process:
    1. Fact extraction: Identify who, what, when from documents
    2. Legal analysis: Score significance and determine if timeline-worthy
    
    Only events with legal_significance_score >= 50 are saved to timeline.
    """
    
    id = fields.IntField(pk=True)
    
    # Links
    case = fields.ForeignKeyField("models.Case", related_name="timeline_events")
    document = fields.ForeignKeyField("models.Document", related_name="timeline_events")
    
    # Extracted Facts (from Fact Extractor Agent)
    actors = fields.JSONField(null=True)  # List of people/orgs involved
    action = fields.CharField(max_length=500)  # What happened
    object_affected = fields.TextField(null=True)  # What was impacted
    
    # Temporal Information
    event_date = fields.DateField(null=True)  # Primary date (ISO format)
    event_date_end = fields.DateField(null=True)  # For date ranges
    date_precision = fields.CharField(max_length=20, default="unknown")  # exact|day|month|year|approximate|unknown
    date_original_text = fields.CharField(max_length=200, null=True)  # Original date string from document
    
    # Legal Analysis (from Legal Analysis Agent)
    legal_significance_score = fields.IntField()  # 0-100 score
    state_changes = fields.JSONField(default=list)  # Which legal state changes triggered
    legal_reasoning = fields.TextField()  # Why this score
    key_factors = fields.JSONField(default=list)  # Key factors influencing score
    
    # Context
    extracted_text = fields.TextField()  # Verbatim quote from document
    extraction_confidence = fields.IntField(default=50)  # Fact extractor confidence (0-100)
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "timeline_events"
        ordering = ["event_date", "created_at"]  # Sort by date, then insertion order
    
    def __str__(self):
        date_str = self.event_date or "Unknown date"
        return f"[{date_str}] {self.action[:50]}"

