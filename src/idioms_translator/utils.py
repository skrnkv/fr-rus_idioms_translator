import json
import re

from parsers import parser_expressio, parser_wiktionary
from sentence_transformers import SentenceTransformer


def read_jsonl(filepath):

    """
    Загружает данные из JSONL файла в список словарей.

    Parameters
    ----------
    filepath : str
        Путь к JSONL файлу.

    Returns
    -------
    data : list of dict
        Список, где каждая строка файла представлена как словарь.
    """
    
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def read_json(path):

    """
    По аналогии с read_jsonl, только для расширения json
    """
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def write_jsonl(file_path, data):

    """
    Сохраняет список словарей в JSONL файл.

    Parameters
    ----------
    filepath : str
        Путь к выходному файлу.
    data : list of dict
        Данные для сохранения.

    Returns
    -------
    None

    Examples
    --------
    >>> idioms = [{"idiom_fr": "prendre une attitude", "best_translation": "занять позицию"}]
    >>> write_jsonl("idioms.jsonl", idioms)
    """

    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


AVAILABLE_SOURCES = {
    "wiktionary": parser_wiktionary,
    "expressio": parser_expressio
}

limits = {"expressio": 3000, "wiktionary": 1500}


def collect_idioms(selected_sources=AVAILABLE_SOURCES.keys(), limit_per_source=limits):

    """
    Сбор идиом из нескольких источников.

    Функция проходит по списку выбранных источников, применяет парсер каждого 
    источника и собирает все найденные идиомы в один список. Ошибки при обработке 
    отдельных источников перехватываются и выводятся, что позволяет продолжить 
    сбор данных с остальных источников.

    Parameters
    ----------
    selected_sources : iterable of str, default=AVAILABLE_SOURCES.keys()
        Список названий источников, из которых необходимо собрать идиомы. 
        Учитываются только источники, присутствующие в `AVAILABLE_SOURCES`.

    limit_per_source : dict, default=limits
        Словарь, задающий максимальное количество идиом для сбора из каждого источника. 
        Ключи словаря должны соответствовать названиям источников.

    Returns
    --------------------
    all_idioms : list
        Список, содержащий все собранные идиомы из указанных источников.
    """

    all_idioms = []

    for source_name in selected_sources:
        parser_module = AVAILABLE_SOURCES[source_name]
        print(f"Сбор данных из {source_name}...")
        try:
            data = parser_module.parse(limit=limit_per_source.get(source_name))
            all_idioms.extend(data)
        except Exception as e:
            print(f"Ошибка при обработке {source_name}: {e}")

    return all_idioms


def clean_idioms(idioms_list):

    """
    Очищает список идиом: убирает дубликаты, чистит контекст, нормализует источники.

    Parameters
    ----------
    idioms_list : list
        Список словарей с ключами 'idiom', 'context', 'source'.

    Returns
    -------
    list
        Список очищенных идиом.
    """

    cleaned_dict = {}
    total = len(idioms_list)
    skipped = 0
    merged = 0

    for item in idioms_list:
        idiom_text = item.get("idiom", "").strip()
        context_text = item.get("context", "").strip() if item.get("context") else ""
        source = item.get("source", "unknown")

        if context_text:
            context_text = re.split(r"—\s*\(", context_text)[0]
            context_text = re.sub(r"\([^)]*\)", " ", context_text)
            context_text = re.sub(r"\s+", " ", context_text).strip()
                
            item["context"] = context_text

        if not idiom_text:
            skipped += 1
            continue

        if source == "expressio":
            idiom_text = re.sub(r"\s*\[.*?\]$", "", idiom_text).strip()

        if source == "wiktionary" and idiom_text and idiom_text[0].isupper():
            skipped += 1
            continue

        if idiom_text in cleaned_dict:
            merged += 1
            existing = cleaned_dict[idiom_text]

            if context_text and context_text not in existing["context"]:
                existing["context"] += (" | " + context_text if existing["context"] else context_text)

            if source not in existing["source"]:
                existing["source"] += f", {source}"

        else:
            cleaned_dict[idiom_text] = {
                "idiom": idiom_text,
                "context": context_text,
                "language": item.get("language", "fr"),
                "source": source
            }
        
    cleaned_list = list(cleaned_dict.values())
    remaining = len(cleaned_list)

    print(f"Статистика очистки:")
    print(f"Всего на входе: {total}")
    print(f"Убрано (пустые/заглавные): {skipped}")
    print(f"Объединено дубликатов: {merged}")
    print(f"Осталось уникальных: {remaining}")

    return cleaned_list
            

model = SentenceTransformer('all-MiniLM-L6-v2')


def create_embeddings_batch(idioms_list, batch_size=50):
    
    """
    Создаёт эмбеддинги для списка идиом с помощью SentenceTransformer.

    Parameters
    ----------
    idioms_list : list
        Список строк (идиомы).
    batch_size : int, optional
        Размер батча при кодировании, по умолчанию 50.

    Returns
    -------
    list
        Список эмбеддингов (list[float]).
    """

    embeddings = []
    for i in range(0, len(idioms_list), batch_size):
        batch = idioms_list[i:i+batch_size]
        batch_emb = model.encode(batch)
        embeddings.extend(batch_emb.tolist())

    return embeddings


if __name__ == "__main__":
    idioms = collect_idioms() 
    print(f"Собрано {len(idioms)} идиом")