{{
    config(
        materialized='table'
    )
}}

with satis_ozeti as (
    -- stg_satis modelinden şehir bazlı agregasyonlar
    select
        sehir,
        count(distinct siparis_id)      as toplam_siparis_sayisi,
        count(distinct musteri_id)      as toplam_musteri_sayisi,
        sum(miktar)                     as toplam_satilan_urun_adedi,
        round(sum(brut_satis_tutari), 2) as toplam_brut_ciro,
        round(sum(net_satis_tutari), 2)  as toplam_net_ciro,
        round(sum(kar_tutari), 2)        as toplam_kar
    from {{ ref('stg_satis') }}
    group by sehir
),

sehir_avm as (
    -- stg_sehir_avm modelinden şehir, bölge ve AVM/nüfus bilgisi
    select
        sehir,
        bolge,
        avm_sayisi,
        nufus_tahmini
    from {{ ref('stg_sehir_avm') }}
),

birlestirilmis as (
    -- Satış özeti ile AVM verisini şehir anahtarı üzerinden birleştir
    select
        s.sehir,
        a.bolge,
        a.avm_sayisi,
        a.nufus_tahmini,

        -- Nüfus & AVM metrikleri
        round(cast(a.nufus_tahmini as double) / nullif(a.avm_sayisi, 0), 0)     as avm_basina_dusen_nufus,

        -- Satış hacmi metrikleri
        s.toplam_siparis_sayisi,
        s.toplam_musteri_sayisi,
        s.toplam_satilan_urun_adedi,
        s.toplam_brut_ciro,
        s.toplam_net_ciro,
        s.toplam_kar,

        -- Kâr marjı ve ortalama sepet metrikleri
        round(s.toplam_net_ciro / nullif(s.toplam_siparis_sayisi, 0), 2)             as ortalama_siparis_tutari,
        round((s.toplam_kar / nullif(s.toplam_net_ciro, 0)) * 100.0, 2)             as kar_marji_yuzdesi,

        -- Dış kaynak ile birleşimden doğan analitik KPI'lar
        round(s.toplam_net_ciro / nullif(a.avm_sayisi, 0), 2)                       as avm_basina_net_ciro,
        round(s.toplam_net_ciro / nullif(cast(a.nufus_tahmini as double), 0), 4)    as kisi_basi_net_ciro

    from satis_ozeti s
    inner join sehir_avm a
        on s.sehir = a.sehir
)

select * from birlestirilmis
