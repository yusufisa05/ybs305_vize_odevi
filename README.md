# YBS305 İş Zekâsı ve Veri Madenciliği - Dönem Projesi (Bölüm 1: dbt ETL & DuckDB)

Bu depo, **YBS305 İş Zekâsı ve Veri Madenciliği** dersi kapsamında geliştirilen uçtan uca veri dönüşüm hattı (ELT/ETL) ve analitik veri ambarı altyapısını içerir.

Proje, **NovaPerakende** operasyonel satış verileri ile Türkiye geneli **Şehir Bazlı AVM ve Nüfus** dış veri setini analitik bir mimaride birleştirerek karar vericilere yönelik kâr, ciro, penetrasyon ve verimlilik metrikleri üretir.

---

## 🏛️ Mimari ve Teknoloji Yığını

- **Analitik Veritabanı (OLAP):** DuckDB (`nova.duckdb`)
- **Dönüşüm & Test Çerçevesi:** dbt Core (`dbt-duckdb` adaptörü)
- **Ham Veri Kaynağı:** `data/perakende_satis.csv` (NovaPerakende)
- **Zenginleştirici Dış Kaynak:** `nova_dbt/seeds/sehir_avm.csv` (Şehir bazlı AVM & tahmini nüfus)
- **Görselleştirme & Dashboard Hedefi:** Power BI Desktop / Streamlit

```
┌────────────────────────────────┐       ┌────────────────────────────────┐
│   Ham Satış Verisi (CSV)       │       │    Dış Kaynak AVM & Nüfus      │
│     (data/perakende_satis)     │       │   (nova_dbt/seeds/sehir_avm)   │
└───────────────┬────────────────┘       └───────────────┬────────────────┘
                │                                        │
                │ (source)                               │ (dbt seed)
                ▼                                        ▼
    ┌───────────────────────┐                ┌───────────────────────┐
    │       stg_satis       │                │     stg_sehir_avm     │
    │  (Temizleme, Tip,     │                │   (Normalizasyon,     │
    │   Finansal Kolonlar)  │                │    LOWER/TRIM)        │
    └───────────┬───────────┘                └───────────┬───────────┘
                │                                        │
                ├───────────────────┐                    │
                │                   ▼                    │
                │         ┌───────────────────┐          │
                │         │    stg_musteri    │          │
                │         │ (Müşteri Özetleri)│          │
                │         └───────────────────┘          │
                │                                        │
                └───────────────────┬────────────────────┘
                                    │
                                    ▼ (INNER JOIN on sehir)
                        ┌────────────────────────┐
                        │  fct_sehir_satis_avm   │
                        │ (Analitik Fact Tablosu)│
                        └────────────────────────┘
```

---

## 📁 Proje Klasör Yapısı

```text
ybs_305_veri_madenciligi_vize_odevi/
├── .gitignore
├── README.md                              # Proje dokümantasyonu ve teslim rehberi
├── data/
│   ├── perakende_satis.csv                # NovaPerakende ham sipariş verileri (UTF-8)
│   ├── perakende_satis.xlsx               # Orijinal kaynak excel tablosu
│   └── sehir_avm.csv                      # Dış kaynak: Şehir, AVM ve nüfus verisi
├── nova_dbt/
│   ├── dbt_project.yml                    # dbt proje ayarları
│   ├── profiles.yml                       # Yerel DuckDB bağlantı profili
│   ├── seeds/
│   │   ├── sehir_avm.csv                  # dbt seed dosyası
│   │   └── schema.yml                     # Seed veri tipleri ve kalite testleri
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml                # data/ altındaki CSV'yi bağlayan harici kaynak
│   │   │   ├── schema.yml                 # Staging modelleri veri sözlüğü ve dbt testleri
│   │   │   ├── stg_satis.sql              # [1. Aşama] Satış verisi temizleme ve tipleme
│   │   │   ├── stg_sehir_avm.sql          # [1. Aşama] AVM verisi normalizasyonu
│   │   │   └── stg_musteri.sql            # [2. Aşama - EKİP ARKADAŞI GÖREVİ] Müşteri boyutu
│   │   └── marts/
│   │       ├── schema.yml                 # Mart modelleri testleri ve dokümantasyonu
│   │       └── fct_sehir_satis_avm.sql    # [2. Aşama - EKİP ARKADAŞI GÖREVİ] Ana Fact tablosu
│   └── tests/                             # Özel veri bütünlüğü testleri
└── venv/                                  # Python sanal ortamı
```

---

## 🚀 1. Aşama: Tamamlanan Altyapı ve Modeller (Yusuf)

1. **Bağlantı & DB:** DuckDB veritabanı bağlantısı (`nova.duckdb`) ve `nova_dbt/profiles.yml` yapılandırıldı.
2. **Seed Katmanı:** `sehir_avm.csv` tohum tablosu eklendi; `schema.yml` üzerinde sütun açıklamaları ve `not_null`, `unique` testleri tanımlandı (`dbt seed` ile 36 şehir yüklendi).
3. **Staging Modelleri:**
   - `stg_satis.sql`: Tarihler `DATE` formatına dönüştürüldü, stringler normalize edildi, hatalı/negatif değerler filtrelendi, `brut_satis_tutari`, `net_satis_tutari`, `toplam_maliyet` ve `kar_tutari` kolonları eklendi.
   - `stg_sehir_avm.sql`: Şehir isimleri `lower(trim(sehir))` ile küçük harf normalize edildi ve tipler dönüştürüldü.
4. **Veri Testleri:** `staging/schema.yml` ve `seeds/schema.yml` içerisinde birincil anahtarlar ve zorunlu alanlar için 24+ dbt testi kurgulandı.
5. **Doğrulama:** `dbt seed`, `dbt run` ve `dbt test` hatasız şekilde başarıyla koşuldu.

---

## 👥 2. Aşama: Ekip Arkadaşı Görev Teslim ve Çalıştırma Rehberi

> [!IMPORTANT]
> Ders kılavuzu gereğince **gruptaki her iki üyenin de GitHub commit geçmişinde aktif katkısı bulunması zorunludur**.
> Ekip arkadaşının kendi bilgisayarında geliştireceği modeller:
> 1. `models/staging/stg_musteri.sql` (Müşteri bazlı agregasyon ve müşteri tekilleştirmesi)
> 2. `models/marts/fct_sehir_satis_avm.sql` (Satışlar ile AVM/Nüfus verisini `sehir` üzerinden JOIN eden ve iş metriklerini hesaplayan ana fact tablosu)
> 3. `models/marts/schema.yml` (Marts katmanı için `relationships` ve `accepted_values` testlerinin doğrulanması ve dokümantasyonun zenginleştirilmesi)

### Adım 1: Depoyu Klonlama ve Çalışma Dalı (Branch) Açma
Terminalinizi açıp depoyu klonlayınız ve kendi adınıza bir feature branch'i oluşturunuz:
```bash
git clone <REPO_URL>
cd ybs_305_veri_madenciligi_vize_odevi

# Kendi çalışma dalınızı oluşturup geçiş yapın
git checkout -b feature/marts-ve-musteri-modelleri
```

### Adım 2: Python Ortamını Hazırlama ve Bağımlılıkları Kurma
```bash
# Python sanal ortamını oluşturun ve aktive edin (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Gerekli kütüphaneleri yükleyin
pip install dbt-duckdb duckdb pandas openpyxl
```

### Adım 3: dbt Bağlantısını ve Profilini Test Etme
`nova_dbt` klasörünün içinde yerel profil mevcuttur. Komutları bu klasörde çalıştırınız:
```bash
cd nova_dbt
dbt debug
```
*(Bağlantının "All checks passed!" verdiğini teyit ediniz.)*

### Adım 4: Tohum Verileri Yükleme ve Mevcut Durumu Çalıştırma
```bash
dbt seed
dbt run
dbt test
```

### Adım 5: Görevleri Tamamlama ve Geliştirme

#### Görev A: `models/staging/stg_musteri.sql`
- Dosyayı açınız. İçerisindeki `TODO 1` ve `TODO 2` yorumlarını inceleyiniz.
- Müşterilerin toplam harcaması, sipariş adedi ve ortalama sepet büyüklüğü gibi metrikleri kontrol edip gerekiyorsa yeni boyutlar (ör. müşteri segmenti, son alışverişten geçen gün sayısı vb.) ekleyiniz.
- Çalıştırma:
  ```bash
  dbt run --select stg_musteri
  dbt test --select stg_musteri
  ```

#### Görev B: `models/marts/fct_sehir_satis_avm.sql`
- Bu model projenin temel iş sorusunu çözer: **"AVM sayısı ve nüfusun satış hacmi ve kârlılığa etkisi nedir?"**
- `models/marts/fct_sehir_satis_avm.sql` dosyasındaki TODO bloklarını inceleyiniz.
- Şehir bazlı `satis_ozeti` CTE'si ile `sehir_avm` CTE'sinin `INNER JOIN` mantığını, hesaplanan `avm_basina_net_ciro` ve `kisi_basi_net_ciro` oranlarını gözden geçirip eklemek istediğiniz diğer KPI'ları (ör. bölge bazlı oranlar) entegre ediniz.
- Çalıştırma:
  ```bash
  dbt run --select fct_sehir_satis_avm
  dbt test --select fct_sehir_satis_avm
  ```

#### Görev C: `models/marts/schema.yml` Testlerini Doğrulama
- Dosyadaki `relationships` (referans bütünlüğü) ve `accepted_values` (geçerli bölge adları) testlerini kontrol ediniz.
- Tüm testleri çalıştırınız:
  ```bash
  dbt test
  ```

### Adım 6: Dashboard'u Başlatma (Streamlit Arayüzü)
Projenin görselleştirme katmanı (Bölüm 1 teslimatı) `app/app.py` üzerinde interaktif olarak hazırdır:
```bash
streamlit run app/app.py
```
Tarayıcınızda açılan ekranda:
- **KPI Kartları:** Toplam Net Ciro, Brüt Kâr, Kâr Marjı, Kapsanan AVM Sayısı ve Ortalama Sepet.
- **İnteraktif Grafikler:** Şehir bazlı ciro/kâr, AVM sayısı vs. satış korelasyonu (Scatter), Bölgesel pasta dağılımı ve AVM başına verimlilik.
- **Filtreler:** Coğrafi bölge, minimum AVM ve ciro dilimleyicileri.
- **Dışa Aktarma:** Power BI veya Excel için CSV indirme butonu.

### Adım 7: dbt Dokümantasyonu Üretme (Kılavuz Gereksinimi)
```bash
cd nova_dbt
dbt docs generate
dbt docs serve
```
Tarayıcınızda açılan dbt kataloğunda veri soy ağacını (Lineage Graph: `raw_data` -> `stg_*` -> `fct_*`) inceleyip ekran görüntüsü alınız.

### Adım 8: Değişiklikleri Commit ve Push Etme
Ders değerlendirmesinde commit geçmişiniz inceleneceği için anlamlı mesajlarla commit atınız:
```bash
git status
git add models/staging/stg_musteri.sql
git commit -m "feat(staging): stg_musteri modeli ve musteri metrikleri tamamlandi"

git add models/marts/fct_sehir_satis_avm.sql models/marts/schema.yml
git commit -m "feat(marts): fct_sehir_satis_avm fact tablosu ve referans butunlugu testleri eklendi"

# Dalınızı GitHub'a gönderin:
git push -u origin feature/marts-ve-musteri-modelleri
```
GitHub arayüzünden `main` dalına bir **Pull Request (PR)** açarak projeyi birleştiriniz.

---

## 📊 Örnek Çıktı: `fct_sehir_satis_avm` Veri Önizlemesi

| Şehir | Bölge | AVM Sayısı | Tahmini Nüfus | Toplam Sipariş | Toplam Net Ciro (TL) | Toplam Kâr (TL) | Kâr Marjı (%) | AVM Başına Ciro (TL) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **İstanbul** | Marmara | 130 | 15.655.000 | 652 | 2.329.220 TL | 808.766 TL | %34.72 | 17.917 TL |
| **Ankara** | İç Anadolu | 41 | 5.803.000 | 296 | 1.018.002 TL | 348.510 TL | %34.23 | 24.829 TL |
| **İzmir** | Ege | 26 | 4.462.000 | 220 | 710.013 TL | 253.354 TL | %35.68 | 27.308 TL |
| **Antalya** | Akdeniz | 18 | 2.688.000 | 150 | 587.284 TL | 221.730 TL | %37.76 | 32.626 TL |
| **Adana** | Akdeniz | 10 | 2.274.000 | 126 | 524.551 TL | 187.548 TL | %35.75 | 52.455 TL |
| **Gaziantep**| Güneydoğu | 9 | 2.154.000 | 135 | 477.033 TL | 159.569 TL | %33.45 | 53.003 TL |
| **Bursa** | Marmara | 15 | 3.194.000 | 111 | 432.740 TL | 154.039 TL | %35.60 | 28.849 TL |
| **Konya** | İç Anadolu | 8 | 2.296.000 | 113 | 388.892 TL | 134.354 TL | %34.55 | 48.611 TL |
| **Trabzon** | Karadeniz | 4 | 818.000 | 99 | 381.523 TL | 133.151 TL | %34.90 | 95.380 TL |
| **Kocaeli** | Marmara | 12 | 2.079.000 | 98 | 357.569 TL | 124.715 TL | %34.88 | 29.797 TL |
