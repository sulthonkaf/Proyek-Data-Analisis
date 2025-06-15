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
sns.lineplot(data=monthly_order, ax=ax1, color="#4C72B0")
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
    sns.barplot(x=order_status_count.index, y=order_status_count.values, color="#4C72B0", ax=ax2)
    ax2.set_title("Distribusi Status Pesanan")
    ax2.set_ylabel("Jumlah")
    ax2.set_xlabel("Status Pesanan")
    plt.xticks(rotation=45)
    st.pyplot(fig2)
    st.markdown("Warna seragam digunakan agar fokus tetap pada perbandingan jumlah, bukan pada variasi warna.")

# -------------------- Lokasi Pelanggan --------------------
st.subheader("Distribusi Lokasi Pelanggan (Sample)")

# Coba cari nama kolom latitude & longitude
lat_col = next((col for col in main_df.columns if 'lat' in col.lower()), None)
lng_col = next((col for col in main_df.columns if 'lng' in col.lower() or 'lon' in col.lower()), None)

if lat_col and lng_col:
    geo_df = main_df.dropna(subset=[lat_col, lng_col])
    if not geo_df.empty:
        geo_df = geo_df.sample(min(1000, len(geo_df)))
        m = folium.Map(location=[-14.2, -51.9], zoom_start=4)
        for _, row in geo_df.iterrows():
            folium.CircleMarker(
                location=[row[lat_col], row[lng_col]],
                radius=1,
                color="blue",
                fill=True,
                fill_opacity=0.5
            ).add_to(m)
        st.markdown(f"Menampilkan peta interaktif dengan sampel {len(geo_df)} titik lokasi pelanggan.")
        st_folium(m, width=700, height=450)
    else:
        st.info("Tidak ada data lokasi yang valid untuk ditampilkan.")
else:
    st.warning("Kolom latitude/longitude tidak ditemukan dalam dataset.")


# -------------------- Review dan Wordcloud --------------------
st.subheader("Distribusi Skor Review Pelanggan")
if "review_score" in main_df.columns and "review_comment_message" in main_df.columns:
    review_score_count = main_df["review_score"].value_counts().sort_index()
    fig3, ax3 = plt.subplots()
    sns.barplot(x=review_score_count.index, y=review_score_count.values, color="#4C72B0", ax=ax3)
    ax3.set_title("Distribusi Skor Review")
    ax3.set_xlabel("Skor")
    ax3.set_ylabel("Jumlah")
    st.pyplot(fig3)
    st.markdown("Visualisasi menggunakan warna tunggal agar tidak melanggar prinsip 'Distract'.")

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
    kategori_terlaris = filtered_df["product_category_name_english"].value_counts().head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    kategori_terlaris.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax)

    for i, v in enumerate(kategori_terlaris):
        ax.text(i, v + 50, str(v), ha='center', fontsize=10)

    ax.set_title('Top 10 Kategori Produk yang Paling Sering Dibeli', fontsize=14)
    ax.set_ylabel('Jumlah Pembelian')
    ax.set_xlabel('Kategori Produk')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Ekspor Data")
    if st.button("Download Top Kategori CSV"):
        csv_data = kategori_terlaris.reset_index()
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
