from parsers import parser_expressio, parser_wiktionary

AVAILABLE_SOURCES = {
    "wiktionary": parser_wiktionary,
    "expressio": parser_expressio
}

limits = {"expressio": 3000, "wiktionary": 1500}


def collect_idioms(selected_sources=AVAILABLE_SOURCES.keys(), limit_per_source=limits):
    
    """
    Сбор идиом из указанных источников.

    Функция обходит список заданных источников, вызывает для каждого соответствующий
    парсер и агрегирует все полученные идиомы в единый список.  
    Подходит для предварительной подготовки корпуса данных из разных источников.

    Parameters
    ----------
    selected_sources : list of str, default=AVAILABLE_SOURCES.keys()
        Список имён источников, из которых требуется собрать идиомы.
        Должны совпадать с ключами в словаре AVAILABLE_SOURCES.

    limit_per_source : dict, default=limits
        Ограничения на количество идиом, извлекаемых из каждого источника.
        Ключи соответствуют названиям источников, значения — целые числа.

    Returns
    -------
    all_idioms : list
        Список идиом, собранных из выбранных источников.
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


if __name__ == "__main__":
    idioms = collect_idioms() 
    print(f"Собрано {len(idioms)} идиом")
