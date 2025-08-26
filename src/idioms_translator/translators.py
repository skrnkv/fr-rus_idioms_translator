import os
import requests
import time
import json
import re

from dotenv import load_dotenv
from transformers import pipeline


load_dotenv()
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")


def translate_yandex(idiom, context="", target_lang="ru", source_lang="fr", retries=5, delay=3):
    """
    Переводит текст с помощью Yandex Translate API.

    Parameters
    ----------
    idiom : str
        Идиома на исходном языке
    context : str, optional
        Контекст, в котором встречается идиома, по умолчанию ""
    target_lang : str, optional
        Код целевого языка (ISO 639-1), по умолчанию "ru"
    source_lang : str, optional
        Код исходного языка (ISO 639-1), по умолчанию "fr"
    retries : int, optional
        Количество попыток при ошибке, по умолчанию 5
    delay : int, optional
        Задержка между повторными попытками в секундах, по умолчанию 3

    Returns
    -------
    str | 
        Переведённый текст или None при неудаче
    """

    if not YANDEX_API_KEY:
        raise ValueError("YANDEX_API_KEY не найден в .env")

    if context:
        text_to_translate = f"{context}\nИдиома: {idiom}"
    else:
        text_to_translate = idiom

    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"

    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    data = {
        "folderId": YANDEX_FOLDER_ID,
        "sourceLanguageCode": source_lang,
        "targetLanguageCode": target_lang,
        "texts": [text_to_translate]
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=data, headers=headers, timeout=15)
            response.raise_for_status()
            result = response.json()

            if "translations" not in result:
                print(f"[Yandex API ERROR] Response: {result}")
                return None

            translated_text = result["translations"][0]["text"]

            if "Идиома:" in translated_text:
                return translated_text.split("Идиома:")[-1].strip()
            return translated_text.strip()

        except Exception as e:
            print(f"[Yandex API] Ошибка при переводе (попытка {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                print("[Yandex API] Все попытки исчерпаны, возвращаю None")
                return None


translator_fr_ru = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-ru")
def translate_hf(idiom, context=""):
    """
    Переводит текст с помощью модели HuggingFace (opus-mt-fr-ru).

    Parameters
    ----------
    idiom : str
        Идиома на французском языке.
    context : str, optional
        Контекст, в котором встречается идиома, по умолчанию "".

    Returns
    -------
    str| 
        Переведённый текст.
    """

    text_to_translate = f"{idiom}. Context: {context}" if context else idiom

    if isinstance(text_to_translate, str):
        text_to_translate = [text_to_translate]

    results = translator_fr_ru(text_to_translate, max_length=512)
    return [res["translation_text"] for res in results][0] 


def verify_translation(idiom, translation_yandex, translation_hf, context=""):
    """
    Сравнивает переводы из Yandex и HuggingFace и выбирает лучший с помощью LLM.

    Parameters
    ----------
    idiom : str
        Французская идиома.
    translation_yandex : str
        Перевод из Yandex Translate.
    translation_hf : str
        Перевод из HuggingFace модели.
    context : str, optional
        Контекст идиомы, по умолчанию "".

    Returns
    -------
    str
        Лучший перевод (по мнению LLM) с подробным описнаием.
    """
    
    if not context:
        context = "Без контекста."

    prompt = f"""
    Ты эксперт по переводу идиом с французского на русский.
    У тебя есть французская идиома: "{idiom}"
    Контекст: "{context}"
    
    Перевод Яндекса: "{translation_yandex}"
    Перевод HuggingFace: "{translation_hf}"
    
    Определи, какой перевод лучше передаёт смысл идиомы с учётом контекста и верни его
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt},
        stream=True
    )

    collected = []
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                collected.append(data["response"])
                
    return "".join(collected).strip()


def extract_translations_from_file(input_file: str, output_file: str = None):
    """
    Читает jsonl, добавляет поля best_translation и candidates в каждый объект
    и перезаписывает файл (или пишет в новый, если указан output_file).
    """
    cleaned_data = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line.strip())
                text = item.get("best_translation", "")  
                candidates = re.findall(r"\"([А-Яа-яЁё\s]+)\"", text)
                
                if candidates:
                    item["best_translation"] = candidates[0].strip()
                
                cleaned_data.append(item)

    if output_file is None:
        output_file = input_file

    with open(output_file, "w", encoding="utf-8") as f:
        for item in cleaned_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


