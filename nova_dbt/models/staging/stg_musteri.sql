{{
    config(
        materialized='view'
    )
}}

/*
===============================================================================
EKİP ARKADAŞI GÖREVİ (TODO: Staging Müşteri Modeli)
===============================================================================
AMAÇ:
Bu model, ham satış hareketlerinden müşteri bazlı tekilleştirilmiş ve özetlenmiş
bir staging görünümü üretir.

BEKLENEN ÇIKTI SÜTUNLARI:
- musteri_id                : Müşteri tekil ID'si (Örn: M0045)
- sehir                     : Müşterinin kayıtlı olduğu şehir (küçük harf normalize)
- bolge                     : Coğrafi bölge
- toplam_siparis_sayisi     : Müşterinin toplam sipariş adedi (COUNT DISTINCT)
- toplam_urun_adedi         : Müşterinin satın aldığı toplam ürün miktarı (SUM)
- toplam_harcama            : Müşterinin toplam net harcaması (SUM(net_satis_tutari))
- ortalama_siparis_tutari   : Sipariş başına ortalama harcama (toplam_harcama / toplam_siparis)
- ilk_siparis_tarihi        : Müşterinin yaptığı ilk alışveriş tarihi (MIN)
- son_siparis_tarihi        : Müşterinin yaptığı en son alışveriş tarihi (MAX)

YÖNERGE:
Aşağıdaki CTE yapısını kullanarak yorum satırları ile belirtilen TODO alanlarını
uygun SQL ifadeleriyle doldurunuz ve `dbt run --select stg_musteri` ile test ediniz.
===============================================================================
*/

with satis_kaynagi as (
    -- TODO 1: stg_satis modelini referans alınız: {{ ref('stg_satis') }}
    select * from {{ ref('stg_satis') }}
),

musteri_ozeti as (
    select
        musteri_id,
        
        -- Şehir ve bölge tekilleştirmesi (En son sipariş verilen şehir veya mode)
        -- Basit yaklaşım: min/max veya grup bazlı ilk değer
        max(sehir) as sehir,
        max(bolge) as bolge,

        -- TODO 2: Aşağıdaki metrikleri hesaplayacak SQL aggregate fonksiyonlarını tamamlayınız:
        count(distinct siparis_id) as toplam_siparis_sayisi,
        sum(miktar) as toplam_urun_adedi,
        round(sum(net_satis_tutari), 2) as toplam_harcama,
        round(sum(net_satis_tutari) / nullif(count(distinct siparis_id), 0), 2) as ortalama_siparis_tutari,
        min(siparis_tarihi) as ilk_siparis_tarihi,
        max(siparis_tarihi) as son_siparis_tarihi

    from satis_kaynagi
    group by musteri_id
)

select * from musteri_ozeti
