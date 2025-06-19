from flask import Flask, render_template, request
import pandas as pd
from collections import defaultdict
import re

app = Flask(__name__)

try:
    df = pd.read_csv('berita_olahraga_scraped.csv')
    required_columns = ['Judul', 'Isi', 'Url', 'Label']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Dataset CSV harus memiliki kolom 'Judul', 'Isi', 'Url', dan 'Label'.")
except FileNotFoundError:
    raise RuntimeError("File 'berita_olahraga_scraped.csv' tidak ditemukan. Pastikan file ada di direktori.")

dokumen = df['Isi'].to_dict()
universal_set = set(dokumen.keys())

def build_inverted_index(docs):
    index = defaultdict(set)
    for doc_id, text in docs.items():
        if isinstance(text, str):
            for word in re.findall(r'\b\w+\b', text.lower()):
                index[word].add(doc_id)
    return index

inverted_index = build_inverted_index(dokumen)

def boolean_search(query):
    tokens = re.findall(r'\b\w+\b', query.lower())
    if not tokens:
        return set()

    def process_term(pos):
        neg = False
        if tokens[pos] == "not":
            neg = True
            pos += 1
            if pos >= len(tokens):
                raise ValueError("Operator NOT harus diikuti oleh sebuah kata.")
        
        word = tokens[pos]
        postings = inverted_index.get(word, set())
        
        if neg:
            return universal_set - postings, pos + 1
        return set(postings), pos + 1

    try:
        result, pos = process_term(0)
        while pos < len(tokens):
            op = tokens[pos]
            if op not in ("and", "or"):
                op = "and"
            else:
                pos += 1
            
            rhs, pos = process_term(pos)
            
            if op == "and":
                result &= rhs
            else: # op == "or"
                result |= rhs
        return result
    except (IndexError, ValueError) as e:
        raise ValueError(f"Query tidak valid: {e}")

@app.route("/", methods=["GET", "POST"])
def index():
    initial_data = df.head(5).to_dict(orient='records')
    for i, record in enumerate(initial_data):
        record['original_index'] = i
    
    search_results = None
    query_text = ""
    error = None

    if request.method == "POST":
        query_text = request.form.get("query", "")
        if query_text:
            try:
                hasil_ids = boolean_search(query_text)
                search_results = df.loc[list(hasil_ids)].to_dict(orient='records')
                for result in search_results:
                    result['original_index'] = result.get('Unnamed: 0', df[df['Judul'] == result['Judul']].index[0])

            except ValueError as e:
                error = str(e)

    return render_template(
        "index.html",
        initial_data=initial_data,
        results=search_results,
        query=query_text,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)

# from flask import Flask, render_template, request
# import pandas as pd
# from collections import defaultdict
# import re

# # Inisialisasi Flask
# app = Flask(__name__)

# # Membaca dataset berita
# df = pd.read_csv('berita_olahraga_scraped.csv')

# # Pastikan kolom 'Judul', 'Isi', 'Url', dan 'Label' ada di CSV
# if 'Judul' not in df.columns or 'Isi' not in df.columns or 'Url' not in df.columns or 'Label' not in df.columns:
#     raise ValueError("Dataset harus memiliki kolom 'Judul', 'Isi', 'Url', dan 'Label'.")

# # Tokenisasi isi berita
# df['Tokens'] = df['Isi'].apply(lambda x: re.findall(r'\b\w+\b', str(x).lower()))

# # Membangun inverted index untuk pencarian boolean
# def build_inverted_index(docs):
#     index = defaultdict(set)0
#     for doc_id, text in docs.items():
#         for word in re.findall(r'\b\w+\b', str(text).lower()):
#             index[word].add(doc_id)
#     return index

# dokumen = df['Isi'].to_dict()
# inverted_index = build_inverted_index(dokumen)
# universal_set = set(dokumen.keys())

# # Fungsi Boolean Search
# def boolean_search(query):
#     tokens = re.findall(r'\b\w+\b', query.lower())
#     if not tokens:
#         return set()

#     def term(pos):
#         neg = False
#         if tokens[pos] == "not":
#             neg = True
#             pos += 1
#             if pos >= len(tokens):
#                 raise ValueError("Operator NOT tidak diikuti term.")
#         word = tokens[pos]
#         postings = set(inverted_index.get(word, set()))
#         if neg:
#             postings = universal_set - postings
#         return postings, pos + 1

#     result, pos = term(0)
#     while pos < len(tokens):
#         op = tokens[pos]
#         if op not in ("and", "or"):
#             raise ValueError(f"Operator tidak dikenali: {op}")
#         pos += 1
#         rhs, pos = term(pos)
#         if op == "and":
#             result &= rhs
#         else:
#             result |= rhs
#     return result

# # Routing utama
# @app.route("/", methods=["GET", "POST"])
# def index():
#     results = []
#     if request.method == "POST":
#         query = request.form.get("query", "")
#         try:
#             hasil_index = boolean_search(query)
#             results = sorted(list(hasil_index))
#         except ValueError as e:
#             results = [str(e)]
#     return render_template("index.html", results=results, df=df.to_dict(orient='index'))

# # Jalankan aplikasi
# if __name__ == "__main__":
#     app.run(debug=True, port=5001)