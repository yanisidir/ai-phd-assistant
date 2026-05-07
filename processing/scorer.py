import json
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "profile.json"

DEFAULT_PROFILE = {
    "interests": [],
    "negative_interests": [],
}


def load_profile():
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as profile_file:
            profile = json.load(profile_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_PROFILE

    return {
        "interests": profile.get("interests", DEFAULT_PROFILE["interests"]),
        "negative_interests": profile.get(
            "negative_interests",
            DEFAULT_PROFILE["negative_interests"],
        ),
    }


def score_offer(offer):
    from ai.llm import ask_llm

    profile = load_profile()
    interests_text = ", ".join(profile.get("interests", []))
    negative_interests_text = ", ".join(profile.get("negative_interests", []))

    prompt = f"""
Analyse cette offre de thèse.

IMPORTANT :
- Score doit être un entier entre 0 et 100
- Si score < 40 → decision = "ignorer"
- Si 40 ≤ score < 70 → decision = "verifier"
- Si score ≥ 70 → decision = "candidater"

Profil :
- intérêts : {interests_text}
- intérêts négatifs : {negative_interests_text}

Offre :
Titre : {offer['title']}
Description : {offer['description']}

Réponds uniquement en JSON :

{{
  "score": int,
  "summary": "...",
  "strengths": ["..."],
  "points_to_check": ["..."],
  "decision": "ignorer / verifier / candidater"
}}
"""

    return ask_llm(prompt)

def score_offer_simple(offer):
    profile = load_profile()
    interests = [keyword.lower() for keyword in profile["interests"]]
    negative_interests = [
        keyword.lower()
        for keyword in profile["negative_interests"]
    ]
    scoring_groups = [
        (interests[0:2], 30),
        (interests[2:5], 20),
        (interests[5:8], 15),
        (interests[8:10], 10),
    ]

    text = " ".join([
        str(offer.get("title", "")),
        str(offer.get("description", "")),
        str(offer.get("laboratory", "")),
    ]).lower()

    score = 0

    for keywords, points in scoring_groups:
        if any(keyword in text for keyword in keywords):
            score += points

    if any(keyword in text for keyword in negative_interests):
        score -= 30

    score = max(0, min(100, score))

    if score >= 60:
        decision = "candidater"
    elif score >= 30:
        decision = "a_verifier"
    else:
        decision = "ignorer"

    return {
        "score": score,
        "decision": decision,
    }
