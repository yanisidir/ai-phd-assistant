def keyword_score(title, description):
    text = (title + " " + description).lower()

    score = 0

    keywords = {
        "particle physics": 25,
        "phenomenology": 25,
        "neutrino": 20,
        "lhc": 20,
        "atlas": 20,
        "cms": 20,
        "cern": 20,
        "machine learning": 20,
        "root": 10,
        "python": 10,
        "c++": 10,
        "cosmology": 10,
        "astroparticle": 10,
        "high energy physics": 20,
        "beyond the standard model": 20,
        "standard model": 15,
        "dark matter": 15
    }

    for keyword, points in keywords.items():
        if keyword in text:
            score += points

    return min(score, 100)


def decision_from_score(score):
    if score >= 70:
        return "candidater"
    elif score >= 40:
        return "verifier"
    else:
        return "ignorer"