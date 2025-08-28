import streamlit as st
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import torch

@st.cache_resource
def load_model():
    model_name = "skrnkv/mt5_idioms_checkpoints_new"
    model = MT5ForConditionalGeneration.from_pretrained(model_name)
    tokenizer = MT5Tokenizer.from_pretrained(model_name)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    
    return model, tokenizer, device

model, tokenizer, device = load_model()

st.title("Переводчик идиом на базе mT5")
st.markdown("Перевод идиом с французского на русский")

text_input = st.text_area("Введите идиому или предложение на французском")

if st.button("Перевести"):
    if text_input.strip():
        text_input_ = "Превод французской идиомы на русский: " + text_input
        inputs = tokenizer([text_input], return_tensors="pt", padding=True, truncation=True).to(device)
        outputs = model.generate(**inputs, max_length=256)
        translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        st.success(f"**Перевод:** {translation}")
    else:
        st.warning("Введите текст для перевода")

