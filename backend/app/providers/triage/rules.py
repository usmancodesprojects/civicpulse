from app.domain import Category, Priority, TriageResult


class RuleBasedTriage:
    name = "rules"

    CATEGORY_TERMS: dict[Category, tuple[str, ...]] = {
        Category.WATER: ("water", "pipe", "sewer", "leak", "flood", "pani", "gutter"),
        Category.ELECTRICITY: ("electric", "wire", "transformer", "power", "bijli", "spark"),
        Category.SANITATION: ("garbage", "trash", "waste", "rubbish", "kachra", "drain"),
        Category.ROADS: ("road", "pothole", "street", "asphalt", "traffic", "gali"),
        Category.STREETLIGHTS: ("streetlight", "street light", "lamp", "dark", "light pole"),
    }
    HIGH_TERMS = (
        "urgent",
        "danger",
        "flood",
        "fire",
        "spark",
        "live wire",
        "injury",
        "entering home",
    )
    LOW_TERMS = ("minor", "faded", "occasionally", "cosmetic")

    def triage(self, text: str, location: str) -> TriageResult:
        normalized = f"{text} {location}".lower()
        category = max(
            self.CATEGORY_TERMS,
            key=lambda item: sum(term in normalized for term in self.CATEGORY_TERMS[item]),
            default=Category.OTHER,
        )
        if not any(term in normalized for term in self.CATEGORY_TERMS.get(category, ())):
            category = Category.OTHER
        priority = Priority.NORMAL
        if any(term in normalized for term in self.HIGH_TERMS):
            priority = Priority.HIGH
        elif any(term in normalized for term in self.LOW_TERMS):
            priority = Priority.LOW
        summary = " ".join(text.strip().split())
        if len(summary) > 137:
            summary = summary[:137].rstrip() + "..."
        return TriageResult(category=category, priority=priority, summary=summary, confidence=0.72)
