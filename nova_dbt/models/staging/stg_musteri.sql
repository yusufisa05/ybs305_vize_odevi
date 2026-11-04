{{
    config(
        materialized='view'
    )
}}

with satis_kaynagi as (
    select * from {{ ref('stg_satis') }}
),

musteri_ozeti as (
    select
        musteri_id,

        -- Şehir ve bölge: en son sipariş verilen değeri al (MAX deterministic yaklaşım)
        max(sehir) as sehir,
        max(bolge) as bolge,

        -- Temel müşteri metrikleri
        count(distinct siparis_id)                                              as toplam_siparis_sayisi,
        sum(miktar)                                                             as toplam_urun_adedi,
        round(sum(net_satis_tutari), 2)                                         as toplam_harcama,
        round(sum(net_satis_tutari) / nullif(count(distinct siparis_id), 0), 2) as ortalama_siparis_tutari,
        min(siparis_tarihi)                                                     as ilk_siparis_tarihi,
        max(siparis_tarihi)                                                     as son_siparis_tarihi

    from satis_kaynagi
    group by musteri_id
)

select * from musteri_ozeti
