import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
from wordcloud import WordCloud
from io import StringIO

# -----------------------------------------------
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")
st.title(" E-Commerce Public Dataset Dashboard")
st.markdown("Visualisasi interaktif untuk memahami data transaksi, kategori produk, dan perilaku pelanggan.")

# -----------------------------------------------
st.sidebar.header(" Filter Waktu")

@st.cache_data
def load_data():
    df = pd.read_csv("Dataset/orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
    return df

df = load_data()
min_date = df["order_purchase_timestamp"].min()
max_date = df["order_purchase_timestamp"].max()
date_range = st.sidebar.date_input("Rentang Tanggal", [min_date, max_date])

if len(date_range) == 2:
    df = df[
        (df["order_purchase_timestamp"] >= pd.to_datetime(date_range[0])) &
        (df["order_purchase_timestamp"] <= pd.to_datetime(date_range[1]))
    ]

# -----------------------------------------------
st.subheader(" Ringkasan Dataset")
col1, col2, col3 = st.columns(3)
col1.metric("Jumlah Pesanan", df["order_id"].nunique())
col2.metric("Jumlah Pelanggan", df["customer_id"].nunique())
col3.metric("Rentang Tanggal", f"{min_date.date()} → {max_date.date()}")

# -----------------------------------------------
st.subheader(" Volume Transaksi per Bulan")
df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
monthly_order = df.groupby("order_month")["order_id"].nunique()

fig1, ax1 = plt.subplots(figsize=(12, 5))
sns.lineplot(data=monthly_order, ax=ax1)
ax1.set_title("Jumlah Pesanan per Bulan")
ax1.set_xlabel("Bulan")
ax1.set_ylabel("Jumlah Pesanan")
plt.xticks(rotation=45)
st.pyplot(fig1)

# -----------------------------------------------
st.subheader(" Distribusi Status Pesanan")
order_status_count = df["order_status"].value_counts()

fig2, ax2 = plt.subplots()
sns.barplot(x=order_status_count.index, y=order_status_count.values, ax=ax2)
ax2.set_title("Distribusi Status Pesanan")
ax2.set_ylabel("Jumlah")
plt.xticks(rotation=45)
st.pyplot(fig2)

# -----------------------------------------------
st.subheader(" Distribusi Lokasi Pelanggan (Sample)")

geo_df = pd.read_csv("Dataset/geolocation_dataset.csv").dropna().sample(1000)
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

# -----------------------------------------------
st.subheader(" Distribusi Skor Review Pelanggan")

if 'review_score' in df.columns and 'review_comment_message' in df.columns:
    review_score_count = df['review_score'].value_counts().sort_index()

    fig3, ax3 = plt.subplots()
    sns.barplot(x=review_score_count.index, y=review_score_count.values, palette='coolwarm', ax=ax3)
    ax3.set_title("Distribusi Skor Review")
    ax3.set_xlabel("Skor")
    ax3.set_ylabel("Jumlah")
    st.pyplot(fig3)

    st.subheader(" Wordcloud Ulasan Pelanggan")
    all_comments = " ".join(df['review_comment_message'].dropna().astype(str).tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_comments)

    fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
    ax_wc.imshow(wordcloud, interpolation='bilinear')
    ax_wc.axis('off')
    st.pyplot(fig_wc)
else:
    st.warning("Kolom `review_score` dan `review_comment_message` tidak tersedia dalam dataset saat ini.")

# -----------------------------------------------
st.sidebar.header(" Filter Kategori Produk")

if 'product_category_name_english' in df.columns:
    kategori_unik = df['product_category_name_english'].dropna().unique()
    selected_kategori = st.sidebar.multiselect("Pilih Kategori Produk", sorted(kategori_unik))
    if selected_kategori:
        df = df[df['product_category_name_english'].isin(selected_kategori)]

st.subheader(" Top 10 Kategori Produk Terlaris")
top_kategori = df['product_category_name_english'].value_counts().head(10)

fig_kat, ax_kat = plt.subplots()
sns.barplot(x=top_kategori.values, y=top_kategori.index, palette='Set2', ax=ax_kat)
ax_kat.set_title("Kategori Produk dengan Pembelian Tertinggi")
ax_kat.set_xlabel("Jumlah Pembelian")
ax_kat.set_ylabel("Kategori")
st.pyplot(fig_kat)

# -----------------------------------------------
# Tombol Ekspor CSV (contoh ekspor top kategori)
st.subheader("⬇️ Ekspor Data")
if st.button("💾 Download Top Kategori CSV"):
    csv_data = top_kategori.reset_index()
    csv_data.columns = ['product_category', 'purchase_count']
    csv_buffer = StringIO()
    csv_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name="top_kategori_produk.csv",
        mime="text/csv"
    )

# -----------------------------------------------
st.markdown("---")
st.caption(" Dibuat oleh **Sulthon Kaffaah** – DBS Coding Camp 2025")
