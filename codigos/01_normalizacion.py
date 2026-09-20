"""Normalización de descripciones usada por la ingesta híbrida Rev44."""

import unicodedata

import pandas as pd


def clean_upper(value):
    if pd.isna(value):
        return pd.NA
    text = " ".join(str(value).strip().split())
    if not text:
        return pd.NA
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char)).upper()
