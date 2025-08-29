# Переводчик идиом с французского на русский на базе mT5



## О проекте

Этот проект реализует **нейросетевой переводчик французских идиом на русский язык** с использованием модели **mT5**.  
Цель проекта — улучшить перевод такой языковой единицы - идиомы - особенно в крайне метафорических языках как французский и русский

---

## Основные возможности
- Перевод идиом с французского на русский с контекстом  
- Вычисление метрик BLEU и Perplexity для оценки модели  
- Быстрая интеграция в веб-приложение через **Streamlit**  

---

## Метрики модели

| Модель                     | BLEU  | Perplexity |
|----------------------------|-------|------------|
| mT5 (моя модель)           | 0.03  | 213.33     |


Вывод: Если смотреть финальный график, то модель демонстрирует способность к обучению, но пока еще уступает уже обученным моделям

## Возможные улучшения

- Сделать более качественную фильтрацию контекста. В нашем случае мы убрали дополнительное объяснение к идиоме (например, что это жаргон), но можно было бы оставить и выделить в отдельный гиперпараметр. И на его базе сперва бы модель классифицировала текст по стилю и это доп/описание могло бы быть подсказкой
- Точно нужно собрать больше идиом, самостоятельный парсинг не выдал желаемого результата
- Почистить идиомы

---

## Установка

1. Клонируем репозиторий:
```
git clone https://github.com/skrnkv/rus-fr_idioms_translator.git
cd rus-fr_idioms_translator
```

2. Создаем виртуальное окружение
```
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```

3. Устанавливаем зависимости
```
pip install --upgrade pip
pip install -r requirements.txt
```

## Установка Hugging Face
```
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("skrnkv/mt5_idioms_checkpoints_new")
model = AutoModelForSeq2SeqLM.from_pretrained("skrnkv/mt5_idioms_checkpoints_new")
```

## Установка FastApi

1. Клонируем репозиторий:
```
git clone https://github.com/skrnkv/rus-fr_idioms_translator.git
cd rus-fr_idioms_translator/docker
```

2. Собираем docker-образ
```
docker build -t idioms-translator
```

3. Запускаем
```
docker run -p 8501:8501 idioms-translator
```


# Запуск приложения
```
cd docker
python3 -m streamlit run web_app.py
```


## Лицензия

MIT License © skrnkv
