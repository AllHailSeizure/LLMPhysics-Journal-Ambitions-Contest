def call_anthropic(messages, model):
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        messages=messages
    )
    return {
        "text": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens
    }