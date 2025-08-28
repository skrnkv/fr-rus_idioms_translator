import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from sentence_transformers import SentenceTransformer

from .utils import clean_idioms, read_jsonl, read_json, write_jsonl
from .translators import translate_yandex, translate_hf, verify_translation, extract_translations_from_file


IDIOMS_FILE = "data/idioms.jsonl"
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2') 


def stage1_translations(backup_files):

    """
    Загружает идиомы, очищает их, строит эмбеддинги и дополняет файл переводами

    Parameters
    ----------
    backup_files : list
        Список файлов-бэкапов (JSON).

    Returns
    -------
    None
    """

    idioms_raw = []
    for file in backup_files:
        idioms_raw.extend(read_json(file))

    print(f"Загружено {len(idioms_raw)} идиом из бэкапов")

    idioms_cleaned = clean_idioms(idioms_raw)
    print(f"Идиомы и контекст очищены")
    data = read_jsonl(IDIOMS_FILE)
    
    idiom_texts = [item["idiom"] for item in idioms_cleaned]
    
    embeddings = EMBEDDING_MODEL.encode(idiom_texts, show_progress_bar=True, batch_size=32)

    existing_ids = [item["id"] for item in data]
    numbers = [int(id[2:]) for id in existing_ids if id.startswith("fr") and id[2:].isdigit()]
    max_num = max(numbers) if numbers else 0

    def process_idiom(idx: int, item: dict, emb):


        new_num = max_num + idx
        new_id = f"fr{new_num:03d}"
        
        translation_yandex = translate_yandex(item["idiom"])
        translation_hf = translate_hf(item["idiom"])

        return {
            "id": new_id,
            "idiom_fr": item["idiom"],
            "context": item.get("context", ""),
            "translation_yandex": translation_yandex,
            "translation_hf": translation_hf,
            "best_translation": None,
            "source": item.get("source", "unknown"),
            "embedding": emb.tolist() if hasattr(emb, "tolist") else emb
        }


    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(process_idiom, idx, item, emb): idx
            for idx, (item, emb) in enumerate(zip(idioms_cleaned, embeddings), start=1)
        }

        for i, future in enumerate(as_completed(futures), start=1):
            start_time = time.time()
            new_entry = future.result()
            data.append(new_entry)

            if i % 20 == 0:
                write_jsonl(IDIOMS_FILE, data)
                total_time = time.time() - start_time
                print(f"Сохранено {len(data)} записей за {total_time:.1f} секунд")

                

    write_jsonl(IDIOMS_FILE, data)
    print(f"Всего добавлено: {len(idioms_cleaned)} идиом")


def stage2_verify_translations_async(batch_size=50, max_workers=5):
    
    """
    Асинхронно проверяет переводы для идиом с помощью LLM и обновляет best_translation

    Parameters
    ----------
    batch_size : int, optional
        Размер батча при обработке, по умолчанию 50.
    max_workers : int, optional
        Количество потоков, по умолчанию 5.

    Returns
    -------
    None
    """
    
    data = read_jsonl(IDIOMS_FILE)
    total = len(data)
    start_time = time.time()


    def process_item(item):
        if not item.get("best_translation"):
            item["best_translation"] = verify_translation(
                idiom=item["idiom_fr"],
                translation_yandex=item["translation_yandex"],
                translation_hf=item["translation_hf"],
                context=item.get("context", "")
            )
        return item

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = data[start:end]

        batch_start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_item, item): idx for idx, item in enumerate(batch)}
            for i, future in enumerate(as_completed(futures), start=1):
                batch[i-1] = future.result()

        data[start:end] = batch
        write_jsonl(IDIOMS_FILE, data)

        batch_time = time.time() - batch_start_time
        elapsed_time = time.time() - start_time
        processed = end
        remaining = total - processed
        est_remaining = (elapsed_time / processed) * remaining if processed else 0

        print(f"Обработано {processed}/{total} идиом | "
              f"Время на батч: {batch_time:.1f}s | "
              f"Прошло: {elapsed_time:.1f}s | "
              f"Осталось ≈ {est_remaining:.1f}s")

    total_time = time.time() - start_time

    extract_translations_from_file(IDIOMS_FILE)

    print(f"Stage 2 завершена за {total_time:.1f} секунд: проверено {total} идиом")

if __name__ == "__main__":

    stage1_translations()
    stage2_verify_translations_async()
