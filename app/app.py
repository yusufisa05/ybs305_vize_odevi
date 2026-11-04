import os
import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# SAYFA YAPILANDIRMASI
# =============================================================================
st.set_page_config(
    page_title="NovaPerakende Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# VERİ YÜKLEME (DuckDB -> Fallback to CSV)
# =============================================================================
@st.cache_data
def load_data():
    """
    Öncelikle dbt tarafından üretilen DuckDB mart tablosunu (fct_sehir_satis_avm) okur.
    Eğer veritabanı kilitli veya bulunamazsa doğrudan CSV'lerden sorgu çalıştırır.
    """
    db_paths = [
        os.path.join("nova_dbt", "nova.duckdb"),
        "nova.duckdb"
    ]
    
    con = None
    for path in db_paths:
        if os.path.exists(path):
            try:
                con = duckdb.connect(database=path, read_only=True)
                df = con.execute("SELECT * FROM fct_sehir_satis_avm").df()
                con.close()
                return df
            except Exception:
                continue

    # Fallback: DuckDB üzerinden CSV'leri canlı birleştirerek fct tablosunu oluştur
    satis_path = os.path.join("data", "perakende_satis.csv")
    avm_path = os.path.join("data", "sehir_avm.csv")
    
    if os.path.exists(satis_path) and os.path.exists(avm_path):
        con = duckdb.connect()
        query = f"""
        with satis_ozeti as (
            select
                lower(trim(Sehir)) as sehir,
                count(distinct SiparisID) as toplam_siparis_sayisi,
                count(distinct Musteri_ID) as toplam_musteri_sayisi,
                sum(Miktar) as toplam_satilan_urun_adedi,
                round(sum(Miktar * BirimFiyat), 2) as toplam_brut_ciro,
                round(sum((Miktar * BirimFiyat) * (1 - IndirimOrani)), 2) as toplam_net_ciro,
                round(sum(((Miktar * BirimFiyat) * (1 - IndirimOrani)) - (Miktar * Maliyet)), 2) as toplam_kar
            from read_csv_auto('{satis_path}')
            group by lower(trim(Sehir))
        ),
        sehir_avm as (
            select
                lower(trim(sehir)) as sehir,
                lower(trim(bolge)) as bolge,
                cast(avm_sayisi as integer) as avm_sayisi,
                cast(nufus_tahmini as bigint) as nufus_tahmini
            from read_csv_auto('{avm_path}')
        )
        select
            s.sehir,
            a.bolge,
            a.avm_sayisi,
            a.nufus_tahmini,
            round(cast(a.nufus_tahmini as double) / nullif(a.avm_sayisi, 0), 0) as avm_basina_dusen_nufus,
            s.toplam_siparis_sayisi,
            s.toplam_musteri_sayisi,
            s.toplam_satilan_urun_adedi,
            s.toplam_brut_ciro,
            s.toplam_net_ciro,
            s.toplam_kar,
            round(s.toplam_net_ciro / nullif(s.toplam_siparis_sayisi, 0), 2) as ortalama_siparis_tutari,
            round((s.toplam_kar / nullif(s.toplam_net_ciro, 0)) * 100.0, 2) as kar_marji_yuzdesi,
            round(s.toplam_net_ciro / nullif(a.avm_sayisi, 0), 2) as avm_basina_net_ciro,
            round(s.toplam_net_ciro / nullif(cast(a.nufus_tahmini as double), 0), 4) as kisi_basi_net_ciro
        from satis_ozeti s
        inner join sehir_avm a on s.sehir = a.sehir
        """
        df = con.execute(query).df()
        con.close()
        return df

    return pd.DataFrame()

df_raw = load_data()

# =============================================================================
# BAŞLIK VE AÇIKLAMA
# =============================================================================
st.title("🛍️ NovaPerakende: Şehir Bazlı Satış & AVM Analitik Panosu")
st.markdown("""
**YBS305 İş Zekâsı ve Veri Madenciliği — Dönem Projesi (Bölüm 1)**  
*Veri Dönüşüm Hattı:* **dbt Core + DuckDB** | *Model:* `fct_sehir_satis_avm` | *Veri Kalitesi:* **46 dbt Testi (0 Hata)**
""")

if df_raw.empty:
    st.error("Veri seti yüklenemedi. Lütfen önce `dbt seed` ve `dbt run` komutlarını çalıştırınız.")
    st.stop()

# Şehir isimlerini düzgün büyük harf yapalım (Görsel şıklık için)
df_display = df_raw.copy()
df_display['sehir_label'] = df_display['sehir'].str.title()
df_display['bolge_label'] = df_display['bolge'].str.title()

# =============================================================================
# YAN PANEL (FİLTRELER / DİLİMLEYİCİLER)
# =============================================================================
st.sidebar.header("🔍 Analiz Filtreleri")

# 1. Filtre: Bölge Seçimi
bolgeler = sorted(df_display['bolge_label'].unique().tolist())
secilen_bolgeler = st.sidebar.multiselect(
    "Coğrafi Bölge Seçin:",
    options=bolgeler,
    default=bolgeler
)

# 2. Filtre: Minimum AVM Sayısı Slider
min_avm = int(df_display['avm_sayisi'].min())
max_avm = int(df_display['avm_sayisi'].max())
secilen_min_avm = st.sidebar.slider(
    "Minimum AVM Sayısı:",
    min_value=min_avm,
    max_value=max_avm,
    value=min_avm
)

# 3. Filtre: Minimum Net Ciro Slider
min_ciro = float(df_display['toplam_net_ciro'].min())
max_ciro = float(df_display['toplam_net_ciro'].max())
secilen_min_ciro = st.sidebar.slider(
    "Minimum Net Ciro (₺):",
    min_value=float(min_ciro),
    max_value=float(max_ciro),
    value=float(min_ciro),
    step=25000.0,
    format="₺%.0f"
)

# Filtreleri uygula
df_filtered = df_display[
    (df_display['bolge_label'].isin(secilen_bolgeler)) &
    (df_display['avm_sayisi'] >= secilen_min_avm) &
    (df_display['toplam_net_ciro'] >= secilen_min_ciro)
]

st.sidebar.markdown("---")
st.sidebar.info(f"Filtrelenen Şehir Sayısı: **{len(df_filtered)} / {len(df_display)}**")

if df_filtered.empty:
    st.warning("Seçilen filtre kriterlerine uygun şehir bulunamadı. Lütfen filtre değerlerini genişletiniz.")
    st.stop()

# =============================================================================
# KPI KARTLARI (EN AZ 3 KPI GEREKSİNİMİ)
# =============================================================================
total_net_ciro = df_filtered['toplam_net_ciro'].sum()
total_kar = df_filtered['toplam_kar'].sum()
avg_kar_marji = (total_kar / total_net_ciro * 100) if total_net_ciro > 0 else 0.0
total_avm = df_filtered['avm_sayisi'].sum()
total_siparis = df_filtered['toplam_siparis_sayisi'].sum()
avg_sepet = (total_net_ciro / total_siparis) if total_siparis > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Toplam Net Ciro", f"₺{total_net_ciro:,.0f}")
col2.metric("Toplam Brüt Kâr", f"₺{total_kar:,.0f}")
col3.metric("Ortalama Kâr Marjı", f"%{avg_kar_marji:.1f}")
col4.metric("Kapsanan AVM Sayısı", f"{total_avm:,}")
col5.metric("Ortalama Sepet Tutarı", f"₺{avg_sepet:,.1f}")

st.markdown("---")

# =============================================================================
# GRAFİKLER (EN AZ 3 GÖRSEL GEREKSİNİMİ)
# =============================================================================
row1_col1, row1_col2 = st.columns(2)

# Görsel 1: Şehir Bazında Net Ciro ve Kâr
with row1_col1:
    st.subheader("📊 1. Şehir Bazında Ciro ve Kâr Performansı")
    df_sorted = df_filtered.sort_values(by="toplam_net_ciro", ascending=True)
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=df_sorted['sehir_label'],
        x=df_sorted['toplam_net_ciro'],
        name='Net Ciro (₺)',
        orientation='h',
        marker_color='#1f77b4'
    ))
    fig_bar.add_trace(go.Bar(
        y=df_sorted['sehir_label'],
        x=df_sorted['toplam_kar'],
        name='Brüt Kâr (₺)',
        orientation='h',
        marker_color='#2ca02c'
    ))
    fig_bar.update_layout(
        barmode='group',
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Tutar (₺)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Görsel 2: AVM Sayısı ile Net Ciro Korelasyonu (İş Sorusu)
with row1_col2:
    st.subheader("🎯 2. AVM Sayısı ile Satış Hacmi İlişkisi")
    fig_scatter = px.scatter(
        df_filtered,
        x="avm_sayisi",
        y="toplam_net_ciro",
        size="nufus_tahmini",
        color="bolge_label",
        hover_name="sehir_label",
        hover_data={"avm_sayisi": True, "toplam_net_ciro": ":,.0f", "kar_marji_yuzdesi": ":.2f%"},
        labels={
            "avm_sayisi": "Şehirdeki AVM Sayısı",
            "toplam_net_ciro": "Toplam Net Ciro (₺)",
            "bolge_label": "Bölge",
            "nufus_tahmini": "Nüfus"
        },
        title="Baloncuk Boyutu: Tahmini Şehir Nüfusu"
    )
    fig_scatter.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

# Görsel 3: Bölgelere Göre Ciro Payı
with row2_col1:
    st.subheader("🥧 3. Bölgelere Göre Net Ciro Dağılımı")
    df_bolge = df_filtered.groupby('bolge_label', as_index=False)['toplam_net_ciro'].sum()
    fig_pie = px.pie(
        df_bolge,
        names="bolge_label",
        values="toplam_net_ciro",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Görsel 4: Verimlilik Metrikleri (AVM Başına Net Ciro)
with row2_col2:
    st.subheader("⚡ 4. AVM Başına Düşen Net Ciro (Verimlilik)")
    df_eff = df_filtered.sort_values(by="avm_basina_net_ciro", ascending=False)
    fig_eff = px.bar(
        df_eff,
        x="sehir_label",
        y="avm_basina_net_ciro",
        color="avm_basina_net_ciro",
        color_continuous_scale="Viridis",
        labels={"sehir_label": "Şehir", "avm_basina_net_ciro": "AVM Başı Ciro (₺)"}
    )
    fig_eff.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_eff, use_container_width=True)

st.markdown("---")

# =============================================================================
# DETAYLI VERİ TABLOSU VE DIŞA AKTARMA (POWER BI / EXCEL ENTEGRASYONU)
# =============================================================================
st.subheader("📋 fct_sehir_satis_avm Analitik Veri Tablosu")

display_cols = [
    'sehir_label', 'bolge_label', 'avm_sayisi', 'nufus_tahmini',
    'toplam_siparis_sayisi', 'toplam_net_ciro', 'toplam_kar',
    'kar_marji_yuzdesi', 'avm_basina_net_ciro', 'kisi_basi_net_ciro'
]

rename_dict = {
    'sehir_label': 'Şehir',
    'bolge_label': 'Bölge',
    'avm_sayisi': 'AVM Sayısı',
    'nufus_tahmini': 'Nüfus',
    'toplam_siparis_sayisi': 'Sipariş Adedi',
    'toplam_net_ciro': 'Net Ciro (₺)',
    'toplam_kar': 'Brüt Kâr (₺)',
    'kar_marji_yuzdesi': 'Kâr Marjı (%)',
    'avm_basina_net_ciro': 'AVM Başı Ciro (₺)',
    'kisi_basi_net_ciro': 'Kişi Başı Ciro (₺)'
}

st.dataframe(
    df_filtered[display_cols].rename(columns=rename_dict).style.format({
        'Nüfus': '{:,.0f}',
        'Sipariş Adedi': '{:,.0f}',
        'Net Ciro (₺)': '₺{:,.2f}',
        'Brüt Kâr (₺)': '₺{:,.2f}',
        'Kâr Marjı (%)': '%{:.2f}',
        'AVM Başı Ciro (₺)': '₺{:,.2f}',
        'Kişi Başı Ciro (₺)': '₺{:.4f}'
    }),
    use_container_width=True
)

# Power BI veya Excel için CSV indirme butonu
csv_bytes = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Tabloyu CSV Olarak İndir (Power BI / Excel Uyumlu)",
    data=csv_bytes,
    file_name="nova_sehir_satis_avm_marts.csv",
    mime="text/csv"
)
