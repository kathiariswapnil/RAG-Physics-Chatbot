from fastapi import FastAPI
from models import SampleRequest
from openai import OpenAI


app = FastAPI()
client = OpenAI()


@app.post("/sample")
def sample(data: SampleRequest):
    response = (
        client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": data.prompt
                }
            ],
            temperature=0
        )
    )
    output = response.choices[0].message.content
    return {"output": output}


@app.get("/health")
def health():
    return {"status": "ok"}