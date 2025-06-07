import streamlit as st
import pandas as pd
import re
from collections import defaultdict

# Membaca dataset
df = pd.read_csv('berita_olahraga_scraped.csv')

# Pastikan kolom 'Judul' dan 'Isi' ada di CSV
if 'Judul' not in df.columns or 'Isi' not in df.columns:
    raise ValueError("Dataset harus memiliki kolom 'Judul' dan 'Isi'.")

# Tokenisasi isi berita
df['Tokens'] = df['Isi'].apply(lambda x: re.findall(r'\b\w+\b', str(x).lower()))

# Membangun inverted index
def build_inverted_index(docs):
    index = defaultdict(set)
    for doc_id, text in docs.items():
        for word in re.findall(r'\b\w+\b', str(text).lower()):
            index[word].add(doc_id)
    return index

dokumen = df['Isi'].to_dict()
inverted_index = build_inverted_index(dokumen)
universal_set = set(dokumen.keys())

# Fungsi Boolean Search
def boolean_search(query):
    tokens = re.findall(r'\b\w+\b', query.lower())
    if not tokens:
        return set()

    def term(pos):
        neg = False
        if tokens[pos] == "not":
            neg = True
            pos += 1
            if pos >= len(tokens):
                raise ValueError("Operator NOT tidak diikuti term.")
        word = tokens[pos]
        postings = set(inverted_index.get(word, set()))
        if neg:
            postings = universal_set - postings
        return postings, pos + 1

    result, pos = term(0)
    while pos < len(tokens):
        op = tokens[pos]
        if op not in ("and", "or"):
            raise ValueError(f"Operator tidak dikenali: {op}")
        pos += 1
        rhs, pos = term(pos)
        if op == "and":
            result &= rhs
        else:
            result |= rhs
    return result

# Aplikasi Streamlit untuk mencari
st.title("Pencarian Berita Olahraga")

query = st.text_input("Masukkan query pencarian (gunakan 'and', 'or', 'not'):")

if query:
    try:
        hasil_index = boolean_search(query)
        results = sorted(list(hasil_index))
        if results:
            st.write("Hasil Pencarian:")
            for result in results:
                st.write(f"- {df.iloc[result]['Judul']}")
        else:
            st.write("Tidak ada hasil ditemukan.")
    except ValueError as e:
        st.error(str(e))
