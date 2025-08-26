import pandas as pd
import numpy as np
import json
import sacrebleu
import torch
import optuna

from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from huggingface_hub import snapshot_download
from transformers import MT5ForConditionalGeneration, MT5Tokenizer, Seq2SeqTrainer
from transformers.training_args_seq2seq import Seq2SeqTrainingArguments
from transformers import DataCollatorForSeq2Seq

df = df[["idiom_fr", "context", "best_translation"]].dropna()
df["input_text"] = df["idiom_fr"] + " [CONTEXT:] " + df["context"]

train_df, test_df = train_test_split(df, test_size=0.15, random_state=42)
train_df, val_df = train_test_split(train_df, test_size=0.15, random_state=42)

dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df),
    "validation": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df)
})

model_name = "google/mt5-small"
tokenizer = MT5Tokenizer.from_pretrained(model_name)

def preprocess_function(examples):
    model_inputs = tokenizer(
        examples["input_text"],
        max_length=128,
        truncation=True,
        padding="max_length"
    )

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            examples["best_translation"],
            max_length=128,
            truncation=True,
            padding="max_length"
        ).input_ids

    labels = [
        [(l if l != tokenizer.pad_token_id else -100) for l in label]
        for label in labels
    ]

    model_inputs["labels"] = labels
    return model_inputs

tokenized_datasets = dataset.map(preprocess_function, batched=True)


model_path = snapshot_download(repo_id="google/mt5-small", cache_dir="./hf_cache")

tokenizer = MT5Tokenizer.from_pretrained(model_path)
model = MT5ForConditionalGeneration.from_pretrained(model_path)