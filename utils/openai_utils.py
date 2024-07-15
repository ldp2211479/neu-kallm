import openai
import os
from openai import OpenAI
import time

def call_openai_api(model, input_text, max_tokens=256, temperature=0, n=1,timeout = 300):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    error_times = 0
    
    while error_times < 5:
        try:
            if "llama" in model:
                client = OpenAI(
                    base_url = 'http://localhost:11434/v1',
                    api_key='ollama', # required, but unused
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": input_text}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=n,
                    timeout=timeout,
                )
                return [response, response.choices[0].message.content]
            elif "text-davinci" in model:
                client = OpenAI()
                # InstructGPT models, text completion
                response = client.chat.completions.create(
                    model=model,
                    prompt=input_text,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=n,
                    timeout=timeout
                )
                return [response, response.choices[0].message.content]
            elif "gpt-" in model:
                client = OpenAI()
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": input_text}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=n,
                    timeout=timeout,
                )
                return [response, response.choices[0].message.content]
            else:
                raise Exception("Invalid model name")
        except Exception as e:
            print('Retry due to:', e)
            error_times += 1
            time.sleep(1)  # Add a delay before retrying
        
    return None

