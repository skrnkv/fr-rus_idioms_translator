from parsers import parser_expressio, parser_wiktionary

AVAILABLE_SOURCES = {
    "wiktionary": parser_wiktionary,
    "expressio": parser_expressio
}

limits = {"expressio": 3000, "wiktionary": 1500}


def collect_idioms(selected_sources=AVAILABLE_SOURCES.keys(), limit_per_source=limits):
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


if __name__ == "__main__":
    idioms = collect_idioms() 
    print(f"Собрано {len(idioms)} идиом")
