import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from matplotlib.lines import Line2D
from collections import Counter

sns.set(style="whitegrid", font_scale=1.2) 

def analyze_and_visualize_idioms(
    file_path, 
    n_components=2, 
    sample_size=1000, 
    method='pca'
):
    """
    Загружает embeddings из файла и визуализирует идиомы в 2D или 3D пространстве.

    Parameters
    ----------
    file_path : str
        Путь к файлу с идиомами (JSONL).
    n_components : int, optional
        Количество компонент для снижения размерности (2 или 3), по умолчанию 2.
    sample_size : int, optional
        Сколько идиом случайно выбрать для визуализации, по умолчанию 1000.
    method : str, optional
        Метод снижения размерности: 'pca' или 'tsne', по умолчанию 'pca'.

    Returns
    -------
    None
        Функция строит график с matplotlib/seaborn.
    """

    cleaned_data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cleaned_data.append(json.loads(line.strip()))

    idioms = [item["idiom_fr"] for item in cleaned_data if item.get("idiom_fr")]
    lengths = [len(idiom.split()) for idiom in idioms]
    sources = [item.get("source", "unknown") for item in cleaned_data]
    has_context = ["yes" if item.get("context") else "no" for item in cleaned_data]

    print(f"Всего уникальных идиом: {len(set(idioms))}")
    print(f"Средняя длина идиомы (в словах): {sum(lengths)/len(lengths):.2f}")

    plt.figure(figsize=(9,6))
    sns.countplot(x=sources, palette="Set2")
    plt.title("Распределение идиом по источникам")
    plt.xlabel("Источник")
    plt.ylabel("Количество")
    plt.show()

    plt.figure(figsize=(9,6))
    sns.histplot(lengths, bins=range(1, max(lengths)+1), kde=False, color="skyblue")
    plt.title("Распределение по длине идиом (в словах)")
    plt.xlabel("Длина идиомы")
    plt.ylabel("Частота")
    plt.show()

    plt.figure(figsize=(9,6))
    sns.countplot(x=has_context, palette="pastel")
    plt.title("Наличие контекста")
    plt.xlabel("Контекст")
    plt.ylabel("Количество")
    plt.show()

    auxiliary_verbs = ["avoir", "être", "faire", "mettre", "prendre", "donner", "passer", "tenir", "aller", "venir"]
    counts = Counter()
    for idiom in idioms:
        tokens = idiom.lower().split()
        for aux in auxiliary_verbs:
            if aux in tokens:
                counts[aux] += 1

    print("\nЧастота вспомогательных глаголов в идиомах:")
    for verb, cnt in counts.most_common():
        print(f"{verb}: {cnt}")

    if counts:
        plt.figure(figsize=(8,5))
        sns.barplot(x=list(counts.keys()), y=list(counts.values()), palette="muted")
        plt.title("Идиомы с вспомогательными глаголами")
        plt.xlabel("Глагол")
        plt.ylabel("Количество")
        plt.show()

    embeddings = [d["embedding"] for d in cleaned_data if "embedding" in d]
    embeddings = np.array(embeddings)

    if len(embeddings) > sample_size:
        idioms = idioms[:sample_size]
        lengths = lengths[:sample_size]
        sources = sources[:sample_size]
        has_context = has_context[:sample_size]
        embeddings = embeddings[:sample_size]

    if method == "pca":
        reducer = PCA(n_components=n_components)
    elif method == "tsne":
        reducer = TSNE(n_components=n_components, perplexity=30, random_state=42, n_iter=1000)
    else:
        raise ValueError("method должен быть 'pca' или 'tsne'")


    X_reduced = reducer.fit_transform(embeddings)

    plt.figure(figsize=(12,8))
    colors = ["#1f77b4" if c == "yes" else "#ff7f0e" for c in has_context]
    plt.scatter(X_reduced[:,0], X_reduced[:,1], c=colors, alpha=0.7, edgecolor="k", s=60)

    plt.title(f"Идиомы: визуализация ({method.upper()}), цвет = наличие контекста")
    plt.xlabel("X")
    plt.ylabel("Y")

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Есть контекст', markerfacecolor="#1f77b4", markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Нет контекста', markerfacecolor="#ff7f0e", markersize=10)
    ]
    plt.legend(handles=legend_elements, loc="best")
    plt.show()


if __name__ == "__main__":
    analyze_and_visualize_idioms("data/idioms.jsonl", method="tsne")



