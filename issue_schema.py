PRIORITY_MAP = {
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3
}

VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}

class Issue:
    def __init__(self, category, title, severity, impact, description, suggestion, location=None, confidence="HIGH"):
        self.category = category
        self.title = title
        self.severity = severity.upper()
        self.priority = PRIORITY_MAP.get(self.severity, 3)
        self.impact = impact
        self.description = description
        self.suggestion = suggestion
        self.location = location
        self.confidence = confidence.upper()
        if self.confidence not in VALID_CONFIDENCE:
            self.confidence = "MEDIUM"
        self.auto_fix = False

    def to_dict(self):
        return {
            "category": self.category,
            "title": self.title,
            "severity": self.severity,
            "priority": self.priority,
            "impact": self.impact,
            "description": self.description,
            "suggestion": self.suggestion,
            "location": self.location,
            "confidence": self.confidence,
            "auto_fix": self.auto_fix
        }

def create_issue(
    category,
    title,
    severity,
    impact,
    description,
    suggestion,
    location=None,
    confidence="HIGH"
):
    """Factory function for backward compatibility."""
    return Issue(
        category,
        title,
        severity,
        impact,
        description,
        suggestion,
        location=location,
        confidence=confidence
    )