# AI PhD Application Assistant

Assistant Python pour rechercher, analyser et preparer des candidatures a des offres de these en physique.

## Objectif

Transformer la recherche de these en pipeline structure :

```text
Scraping -> Parsing -> IA -> Stockage -> Interface
```

Le projet combine scraping web, nettoyage de donnees, analyse par LLM local avec Ollama, generation de mails et suivi des candidatures.

## Etat actuel

V1 prototype :

- une offre simulee dans `scraping/academic_positions.py`
- normalisation des offres dans `processing/parser.py`
- scoring LLM dans `processing/scorer.py`
- gestion explicite des erreurs Ollama dans `ai/llm.py`
- affichage console dans `main.py`

## Lancer le prototype

```bash
source venv/bin/activate
python main.py
```

Pour obtenir une vraie analyse IA, Ollama doit etre lance et le modele `llama3.1` doit etre disponible localement.

## Roadmap

1. Prototype console robuste
2. Scraping reel Academic Positions
3. Scoring structure au format JSON
4. Stockage SQLite
5. Generation de mails personnalises
6. Interface Streamlit
7. Multi-sources : Euraxess, InspireHEP, laboratoires, universites

La vision detaillee est conservee dans `recap.txt`.
