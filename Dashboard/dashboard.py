import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import zipfile
from streamlit_folium import st_folium
from wordcloud import WordCloud
from io import StringIO
import os

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

# -------------------- Sidebar Identitas --------------------
logo_path = os.path.join("Assets", "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, caption="Sistem Analisis E-Commerce", use_container_width=True)

st.sidebar.header("Tentang Developer")
st.sidebar.markdown("""
- Nama: Sulthon Kaffaah Al Farizzi  
- Email: sulthonkaffaah@gmail.com  
- Universitas: Universitas Muhammadiyah Surakarta  
- ID Dicoding: sulthonkaf  
""")
st.sidebar.markdown("""
Dashboard ini dibuat untuk menganalisis dataset publik E-Commerce Brazil, meliputi:
- Volume transaksi bulanan  
- Distribusi status pesanan  
- Ulasan pelanggan  
- Kategori produk terlaris  
- Visualisasi geolokasi pelanggan  
""")

# -------------------- Load Dataset --------------------


@st.cache_data
def load_main_data():
    zip_path = "Dashboard/main_data.zip"
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path) as z:
            with z.open("main_data.csv") as f:
                return pd.read_csv(f, low_memory=False)
    st.error("File main_data.zip tidak ditemukan.")
    return pd.DataFrame()


main_df = load_main_data()

if main_df.empty or "order_purchase_timestamp" not in main_df.columns:
    st.error("Dataset tidak valid atau kolom waktu tidak ditemukan.")
    st.stop()

main_df["order_purchase_timestamp"] = pd.to_datetime(main_df["order_purchase_timestamp"])

# -------------------- Filter Waktu --------------------
st.sidebar.header("Filter Waktu")
min_date = main_df["order_purchase_timestamp"].min()
max_date = main_df["order_purchase_timestamp"].max()
date_range = st.sidebar.date_input("Rentang Tanggal", [min_date, max_date])

if len(date_range) == 2:
    main_df = main_df[
        (main_df["order_purchase_timestamp"] >= pd.to_datetime(date_range[0])) &
        (main_df["order_purchase_timestamp"] <= pd.to_datetime(date_range[1]))
    ]

# -------------------- Ringkasan Dataset --------------------
st.title("E-Commerce Public Dataset Dashboard")
st.markdown("Visualisasi interaktif untuk memahami data transaksi, kategori produk, dan perilaku pelanggan.")
st.subheader("Ringkasan Dataset")
col1, col2, col3 = st.columns(3)
col1.metric("Jumlah Pesanan", main_df["order_id"].nunique())
col2.metric("Jumlah Pelanggan", main_df["customer_id"].nunique())
col3.metric("Rentang Tanggal", f"{min_date.date()} → {max_date.date()}")

# -------------------- Volume Transaksi Bulanan --------------------
st.subheader("Volume Transaksi per Bulan")
main_df["order_month"] = main_df["order_purchase_timestamp"].dt.to_period("M").astype(str)
monthly_order = main_df.groupby("order_month")["order_id"].nunique()

fig1, ax1 = plt.subplots(figsize=(12, 5))
sns.lineplot(data=monthly_order, ax=ax1)
ax1.set_title("Jumlah Pesanan per Bulan")
ax1.set_xlabel("Bulan")
ax1.set_ylabel("Jumlah Pesanan")
plt.xticks(rotation=45)
st.pyplot(fig1)

# -------------------- Status Pesanan --------------------
st.subheader("Distribusi Status Pesanan")
if "order_status" in main_df.columns:
    order_status_count = main_df["order_status"].value_counts()
    fig2, ax2 = plt.subplots()
    sns.barplot(x=order_status_count.index, y=order_status_count.values, ax=ax2)
    ax2.set_title("Distribusi Status Pesanan")
    ax2.set_ylabel("Jumlah")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# -------------------- Lokasi Pelanggan --------------------
st.subheader("Distribusi Lokasi Pelanggan (Sample)")
if "geolocation_lat" in main_df.columns and "geolocation_lng" in main_df.columns:
    geo_df = main_df.dropna(subset=["geolocation_lat", "geolocation_lng"]).sample(1000)
    m = folium.Map(location=[-14.2, -51.9], zoom_start=4)
    for _, row in geo_df.iterrows():
        folium.CircleMarker(
            location=[row["geolocation_lat"], row["geolocation_lng"]],
            radius=1,
            color="blue",
            fill=True,
            fill_opacity=0.5
        ).add_to(m)
    st_folium(m, width=700, height=450)

# -------------------- Review dan Wordcloud --------------------
st.subheader("Distribusi Skor Review Pelanggan")
if "review_score" in main_df.columns and "review_comment_message" in main_df.columns:
    review_score_count = main_df["review_score"].value_counts().sort_index()
    fig3, ax3 = plt.subplots()
    sns.barplot(x=review_score_count.index, y=review_score_count.values, palette='coolwarm', ax=ax3)
    ax3.set_title("Distribusi Skor Review")
    ax3.set_xlabel("Skor")
    ax3.set_ylabel("Jumlah")
    st.pyplot(fig3)

    st.subheader("Wordcloud Ulasan Pelanggan")
    all_comments = " ".join(main_df["review_comment_message"].dropna().astype(str).tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_comments)
    fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
    ax_wc.imshow(wordcloud, interpolation='bilinear')
    ax_wc.axis("off")
    st.pyplot(fig_wc)

# -------------------- Kategori Produk Terlaris --------------------
st.sidebar.header("Filter Kategori Produk")
if "product_category_name_english" in main_df.columns:
    kategori_unik = main_df["product_category_name_english"].dropna().unique()
    selected_kategori = st.sidebar.multiselect("Pilih Kategori Produk", sorted(kategori_unik))
    filtered_df = main_df[main_df["product_category_name_english"].isin(selected_kategori)] if selected_kategori else main_df

    st.subheader("Top 10 Kategori Produk Terlaris")
    top_kategori = filtered_df["product_category_name_english"].value_counts().head(10)

    fig_kat, ax_kat = plt.subplots()
    sns.barplot(x=top_kategori.values, y=top_kategori.index, palette="Set2", ax=ax_kat)
    ax_kat.set_title("Kategori Produk dengan Pembelian Tertinggi")
    ax_kat.set_xlabel("Jumlah Pembelian")
    ax_kat.set_ylabel("Kategori")
    st.pyplot(fig_kat)

    st.subheader("Ekspor Data")
    if st.button("Download Top Kategori CSV"):
        csv_data = top_kategori.reset_index()
        csv_data.columns = ['product_category', 'purchase_count']
        csv_buffer = StringIO()
        csv_data.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Unduh CSV",
            data=csv_buffer.getvalue(),
            file_name="top_kategori_produk.csv",
            mime="text/csv"
        )

# -------------------- Footer --------------------
st.markdown("---")
st.caption("Dibuat oleh Sulthon Kaffaah Al Farizzi - DBS Coding Camp 2025")
