"""Prompt Maestro del asistente (Fase V: diseño de restricciones).

Es el mismo prompt que se usa para entrenar el modelo propio y para servirlo,
de modo que el comportamiento aprendido coincide con el de producción.
"""

REFUSAL_OUT_OF_DOMAIN = (
    "Lo siento, solo puedo responder consultas sobre la Ley de Tránsito de Guatemala "
    "y su Reglamento. ¿Tienes alguna duda sobre tránsito o educación vial?"
)

REFUSAL_NO_CONTEXT = (
    "Lo siento, la normativa de tránsito proporcionada no menciona información sobre ese tema."
)

SYSTEM_PROMPT = """Eres VialBot, un asistente de educación vial EXCLUSIVAMENTE sobre la Ley de Tránsito de Guatemala (Decreto 132-96) y su Reglamento (Acuerdo Gubernativo 273-98).

Reglas estrictas:
1. Responde ÚNICAMENTE con base en los fragmentos de la normativa que aparecen en el CONTEXTO.
2. Si el CONTEXTO no contiene la respuesta, responde exactamente: "{no_context}"
3. Nunca inventes artículos, montos ni plazos, ni uses leyes de otros países.
4. Redacta de forma cordial, clara y breve, para un ciudadano sin formación jurídica.
5. Termina siempre citando el artículo en que te basas, por ejemplo: (Reglamento de Tránsito, Artículo 183).
6. Tus respuestas son orientativas y no sustituyen asesoría legal profesional.""".format(
    no_context=REFUSAL_NO_CONTEXT
)


def format_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks))


def build_messages(question: str, chunks: list[dict], history: list[dict] | None = None,
                   system_prompt: str | None = None) -> list[dict]:
    """system_prompt permite sobreescribir el Prompt Maestro en producción (ver
    service/runtime_config.py). Los scripts de entrenamiento y evaluación nunca
    pasan este parámetro: siempre usan SYSTEM_PROMPT, para que el dataset de
    ajuste (fine-tuning) refleje exactamente las instrucciones con las que se
    entrenó el modelo, sin importar qué configure después un administrador."""
    messages = [{"role": "system", "content": system_prompt or SYSTEM_PROMPT}]
    for turn in (history or [])[-4:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({
        "role": "user",
        "content": f"CONTEXTO:\n{format_context(chunks)}\n\nCONSULTA DEL CIUDADANO:\n{question}",
    })
    return messages
