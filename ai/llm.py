import ollama


class LLMError(RuntimeError):
    """Raised when the local LLM cannot return a usable answer."""


def ask_llm(prompt, model="mistral"):
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
    except Exception as exc:
        raise LLMError(
            "Impossible de contacter Ollama. Vérifie qu'Ollama est lancé "
            f"et que le modèle '{model}' est installé."
        ) from exc

    try:
        return response["message"]["content"]
    except KeyError as exc:
        raise LLMError("Réponse Ollama inattendue : contenu manquant.") from exc
