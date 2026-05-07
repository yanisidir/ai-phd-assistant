DEFAULT_CANDIDATE_PROFILE = {
    "degree": "Master en physique subatomique",
    "skills": ["Python", "C++", "ROOT", "machine learning"],
    "interests": [
        "physique des particules",
        "phénoménologie",
        "analyse de données",
        "neutrinos",
        "LHC",
    ],
}


def build_scoring_prompt(offer, candidate_profile=None):
    profile = candidate_profile or DEFAULT_CANDIDATE_PROFILE
    skills = ", ".join(profile["skills"])
    interests = ", ".join(profile["interests"])

    return f"""
Tu es un assistant spécialisé dans l'analyse d'offres de thèse.

Profil candidat :
- {profile["degree"]}
- Compétences : {skills}
- Intérêts : {interests}

Offre :
Titre : {offer["title"]}
Description : {offer["description"]}
Lien : {offer["link"]}
Laboratoire : {offer["laboratory"]}
Localisation : {offer["location"]}
Date limite : {offer["deadline"]}

Réponds avec :
1. Score de pertinence /100
2. Résumé en 5 lignes
3. Compétences du candidat à mettre en avant
4. Points à vérifier avant candidature
5. Avis : candidater / à vérifier / ignorer
"""
