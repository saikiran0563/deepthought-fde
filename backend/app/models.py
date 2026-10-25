from datetime import datetime, timezone

from app import db


def utc_now():
    return datetime.now(timezone.utc)


class Call(db.Model):
    __tablename__ = "calls"

    id = db.Column(db.Integer, primary_key=True)
    prospect_name = db.Column(db.String(120), nullable=False, default="Unknown")
    company_name = db.Column(db.String(160), nullable=False, default="")
    current_stage = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="in_progress")

    prospect_words = db.Column(db.Text, nullable=False, default="")
    notes = db.Column(db.Text, nullable=False, default="")
    outcome = db.Column(db.String(80), nullable=False, default="No outcome logged")
    next_step = db.Column(db.Text, nullable=False, default="")

    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "prospect_name": self.prospect_name,
            "company_name": self.company_name,
            "current_stage": self.current_stage,
            "stage_name": next(
                (s["name"] for s in __import__(
                    "app.config", fromlist=["CALL_STAGES"]
                ).CALL_STAGES if s["id"] == self.current_stage),
                "Unknown"
            ),
            "status": self.status,
            "prospect_words": self.prospect_words,
            "notes": self.notes,
            "outcome": self.outcome,
            "next_step": self.next_step,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
