import uuid

from app.db import session_scope
from app.domain import ComplaintCreate
from app.providers.cache import get_redis
from app.providers.triage.rules import RuleBasedTriage
from app.repositories.complaints import ComplaintRepository

SEED_DATA = [
    (
        "Pani ki main pipe phat gayi, road flood ho rahi hai aur ghar mein pani aa raha hai",
        "Street 12, G-10",
    ),
    ("Transformer se sparks aa rahe hain, bachay qareeb khel rahe hain", "Block C, Satellite Town"),
    ("Kachra teen din se collect nahi hua aur smell bohat zyada hai", "Lane 4, Gulshan Colony"),
    ("Main road par gehra pothole hai, bikes slip kar rahi hain", "College Road near Gate 2"),
    ("Street light do haftay se band hai aur gali bilkul dark hai", "House 28, Street 7"),
    ("Sewer overflow ho raha hai, pani shops ke andar ja raha hai", "Bazar Road, Committee Chowk"),
    ("Bijli ki live wire neeche latak rahi hai, urgent danger", "Pole 19, Model Town"),
    ("Garbage container full hai aur waste road par phail gaya", "Park entrance, Sector F"),
    ("Road surface toot chuki hai after rain, cars damage ho rahi hain", "Canal View Road"),
    ("Lamp pole flicker karta hai aur phir poori raat off rehta hai", "Street 22, I-8"),
    ("Water supply mein leakage hai, pressure bohat low ho gaya", "Lane 9, Westridge"),
    ("Power outage since fajr, poora block affected hai", "Block A, Bahria Phase 4"),
    ("Drain mein plastic jam hai aur badboo aa rahi hai", "Market Lane, Saddar"),
    ("Speed breaker ka paint faded hai, minor safety issue", "School Road, F-7"),
    ("Two streetlights damaged after storm", "Main Boulevard, DHA 2"),
    ("Public tap continuously leak kar raha hai", "Bus stop near Kacheri"),
    ("Electric meter box open hai and wires exposed hain", "Shop 16, Raja Bazar"),
    ("Waste pickup missed our mohalla again", "Mohalla Rehmatabad"),
    ("Footpath broken and elderly people cannot walk safely", "Hospital Road"),
    ("Light pole leaning towards road after accident", "Murree Road U-turn"),
    ("Gutter ka pani school gate ke samne khara hai", "Government School, Chaklala"),
    ("Transformer makes loud noise occasionally", "Phase 1 commercial area"),
    ("Dead animal removal required from roadside", "Airport Housing Society"),
    ("Potholes across service lane causing traffic jam", "Expressway service road"),
    ("Street light timer turns off too early", "Park Road, Bani Gala"),
    ("Water is muddy since pipeline repair", "Street 5, Muslim Town"),
    ("Repeated voltage fluctuation damaged appliances", "Block D, PWD"),
    ("Construction debris dumped beside community park", "Sector E-11"),
    ("Road sign has fallen and blocks one lane", "Kashmir Highway interchange"),
    ("Tree branches cover the streetlamp", "Lane 3, Shalimar Colony"),
    ("Unknown abandoned cart blocks pedestrian crossing", "Commercial Market crossing"),
    ("Pani tanker spilled diesel-like liquid, please inspect", "Depot Road"),
]


def seed() -> int:
    inserted = 0
    rules = RuleBasedTriage()
    with session_scope() as session:
        repository = ComplaintRepository(session)
        for text, location in SEED_DATA:
            complaint_id = uuid.uuid5(uuid.NAMESPACE_URL, f"civicpulse:{text}|{location}")
            if repository.exists(complaint_id):
                continue
            payload = ComplaintCreate(text=text, location=location)
            result = rules.triage(text, location)
            repository.create(complaint_id, payload, result, "rules", 1)
            inserted += 1
    get_redis().delete("stats:v1")
    return inserted


if __name__ == "__main__":
    count = seed()
    print(f"Seed complete: {count} new complaints")
