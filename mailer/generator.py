from ai.llm import ask_llm

def generate_email(offer):

    prompt = f"""
Tu es un candidat qui postule à une thèse.

Rédige un mail de candidature professionnel, clair et concis.

Informations :
- Nom : Mohamed Yanis IDIR
- Formation : Master physique subatomique
- Compétences : Python, C++, ROOT, machine learning
- Expérience : stage en calorimétrie hadronique + ML

Offre :
Titre : {offer['title']}
Description : {offer['description']}

Le mail doit :
- être formel
- être personnalisé pour cette offre
- être court (10-15 lignes max)
"""

    return ask_llm(prompt)