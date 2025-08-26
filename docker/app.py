from fastapi import FastAPI
from pydantic import BaseModel
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import torch

app = FastAPI()

model_name = "skrnkv/final_results"
model = MT5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = MT5Tokenizer.from_pretrained(model_name)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

class TranslateRequest(BaseModel):
    text: str

@app.post("/translate")
def translate(req: TranslateRequest):
    text_input = "translate French idiom to Russian: " + req.text
    inputs = tokenizer([text_input], return_tensors="pt", padding=True, truncation=True).to(device)
    outputs = model.generate(**inputs, max_length=128)
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"translation": translation}
