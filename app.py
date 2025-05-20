import streamlit as st
from newspaper import Article
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import io

def get_article_links(base_url, page_num):
    """
    Fungsi contoh untuk scrape link artikel dari halaman beranda/pagination.
    **HARUS disesuaikan dengan situs target.**
    """
    url = f"{base_url}/page/{page_num}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    # Contoh ambil semua link <a> yang mungkin berita, harus disesuaikan!
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') and href not in links:
            links.append(href)
    return links

def filter_by_date(article, days_limit):
    # newspaper tidak selalu dapat tanggal, ini contoh default True
    try:
        pub_date = article.publish_date
        if pub_date:
            return pub_date >= datetime.now() - timedelta(days=days_limit)
    except:
        pass
    return True  # Jika tanggal tidak dapat, tetap dianggap valid

def filter_by_keyword(title, keyword):
    return keyword.lower() in title.lower()

def filter_by_word_count(text, min_words):
    return len(text.split()) >= min_words

st.title("Scraping Berita Dinamis")

base_url = st.text_input("Masukkan URL situs berita (contoh: https://news.example.com)", value="https://news.example.com")
keyword = st.text_input("Masukkan kata kunci judul berita untuk filter", value="")
days = st.number_input("Berita dalam berapa hari ke belakang?", min_value=1, max_value=30, value=7)
pages = st.number_input("Jumlah halaman yang ingin discan (pagination)", min_value=1, max_value=10, value=2)
min_words = st.number_input("Minimal kata isi berita", min_value=0, max_value=2000, value=100)

if st.button("Mulai Scraping"):
    all_results = []

    with st.spinner("Sedang scraping..."):
        for page in range(1, pages + 1):
            try:
                links = get_article_links(base_url, page)
            except Exception as e:
                st.error(f"Gagal ambil link dari halaman {page}: {e}")
                continue

            for link in links:
                try:
                    article = Article(link, language='id')
                    article.download()
                    article.parse()
                except:
                    continue

                if not article.title or not article.text:
                    continue

                if keyword and not filter_by_keyword(article.title, keyword):
                    continue

                if not filter_by_date(article, days):
                    continue

                if not filter_by_word_count(article.text, min_words):
                    continue

                all_results.append({
                    'Judul': article.title,
                    'URL': link,
                    'Tanggal': article.publish_date if article.publish_date else 'Unknown',
                    'Isi (potongan)': article.text[:200] + '...',
                    'Jumlah Kata': len(article.text.split())
                })

    if all_results:
        df = pd.DataFrame(all_results)
        st.dataframe(df)

        # Ekspor CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='hasil_scraping_berita.csv',
            mime='text/csv'
        )
    else:
        st.warning("Tidak ditemukan berita yang sesuai kriteria.")
