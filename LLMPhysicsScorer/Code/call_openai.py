def call_openai(messages, model):
    """
    Calls the OpenAI API and returns a normalized response dict.
    """
    response = openai_client.chat.completions.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        messages=messages
    )
    return {
        "text": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens
    }