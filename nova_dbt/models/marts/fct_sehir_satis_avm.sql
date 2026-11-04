{{
    config(
        materialized='table'
    )
}}

/*
===============================================================================
EKİP ARKADAŞI GÖREVİ (TODO: Ana Mart Fact Tablosu - fct_sehir_satis_avm)
===============================================================================
İŞ PROBLEMİ / AMAÇ:
Şehir bazındaki AVM sayıları ve nüfus yoğunluğunun, perakende satış hacmi,
müşteri sayısı, sepet büyüklüğü ve kârlılık üzerindeki etkisini ölçmek.
Bu tablo Power BI dashboard ve veri madenciliği modellerine girdi sağlayacak
temel analitik fact tablosudur.

BEKLENEN ÇIKTI SÜTUNLARI:
- sehir                     : Şehir adı (Birincil anahtar / Grain)
- bolge                     : Coğrafi bölge
- avm_sayisi                : Şehirdeki toplam AVM adedi
- nufus_tahmini             : Şehrin tahmini nüfusu
- avm_basina_dusen_nufus    : nufus_tahmini / avm_sayisi
- toplam_siparis_sayisi     : Şehirden verilen benzersiz sipariş adedi
- toplam_musteri_sayisi     : Şehirdeki tekil müşteri sayısı
- toplam_satilan_urun_adedi : Şehirde satılan toplam ürün adedi
- toplam_brut_ciro          : İndirim öncesi brüt satış hasılatı
- toplam_net_ciro           : İndirim sonrası elde edilen net ciro
- toplam_kar                : Şehir bazında brüt kâr (Ciro - Maliyet)
- ortalama_siparis_tutari   : Sipariş başına ortalama sepet büyüklüğü
- kar_marji_yuzdesi         : Kâr / Net Ciro oranı (%)
- avm_basina_net_ciro       : toplam_net_ciro / avm_sayisi
- kisi_basi_net_ciro        : toplam_net_ciro / nufus_tahmini

YÖNERGE:
1. `satis_ozeti` CTE'sinde stg_satis modelinden şehir bazlı agregasyonları yapınız.
2. `sehir_avm` CTE'sinde stg_sehir_avm modelini referans alınız.
3. Final sorgusunda iki CTE'yi `sehir` anahtarı üzerinden JOIN edip analitik oranları hesaplayınız.
===============================================================================
*/

with satis_ozeti as (
    -- TODO 1: stg_satis modelinden şehir bazlı agregasyonları oluşturunuz
    select
        sehir,
        count(distinct siparis_id) as toplam_siparis_sayisi,
        count(distinct musteri_id) as toplam_musteri_sayisi,
        sum(miktar) as toplam_satilan_urun_adedi,
        round(sum(brut_satis_tutari), 2) as toplam_brut_ciro,
        round(sum(net_satis_tutari), 2) as toplam_net_ciro,
        round(sum(kar_tutari), 2) as toplam_kar
    from {{ ref('stg_satis') }}
    group by sehir
),

sehir_avm as (
    -- TODO 2: stg_sehir_avm modelini referans alınız
    select
        sehir,
        bolge,
        avm_sayisi,
        nufus_tahmini
    from {{ ref('stg_sehir_avm') }}
),

birlestirilmis as (
    -- TODO 3: Satış özeti ile Şehir AVM verisini 'sehir' kolonu üzerinden birleştiriniz (JOIN)
    select
        s.sehir,
        a.bolge,
        a.avm_sayisi,
        a.nufus_tahmini,
        
        -- Nüfus & AVM metrikleri
        round(cast(a.nufus_tahmini as double) / nullif(a.avm_sayisi, 0), 0) as avm_basina_dusen_nufus,

        -- Satış hacmi metrikleri
        s.toplam_siparis_sayisi,
        s.toplam_musteri_sayisi,
        s.toplam_satilan_urun_adedi,
        s.toplam_brut_ciro,
        s.toplam_net_ciro,
        s.toplam_kar,

        -- Kâr marjı ve ortalama sepet metrikleri
        round(s.toplam_net_ciro / nullif(s.toplam_siparis_sayisi, 0), 2) as ortalama_siparis_tutari,
        round((s.toplam_kar / nullif(s.toplam_net_ciro, 0)) * 100.0, 2) as kar_marji_yuzdesi,

        -- Dış kaynak ile birleşimden doğan analitik KPI'lar
        round(s.toplam_net_ciro / nullif(a.avm_sayisi, 0), 2) as avm_basina_net_ciro,
        round(s.toplam_net_ciro / nullif(cast(a.nufus_tahmini as double), 0), 4) as kisi_basi_net_ciro

    from satis_ozeti s
    inner join sehir_avm a
        on s.sehir = a.sehir
)

select * from birlestirilmis
