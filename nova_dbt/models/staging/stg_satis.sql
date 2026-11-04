with raw_satis as (
    select * from {{ source('raw_data', 'perakende_satis') }}
),

cleaned as (
    select
        cast(SiparisID as varchar) as siparis_id,
        cast(Tarih as date) as siparis_tarihi,
        cast(Musteri_ID as varchar) as musteri_id,
        lower(trim(Sehir)) as sehir,
        lower(trim(Bolge)) as bolge,
        lower(trim(Kanal)) as kanal,
        lower(trim(Kategori)) as kategori,
        trim(Urun) as urun_adi,
        cast(Miktar as integer) as miktar,
        cast(BirimFiyat as double) as birim_fiyat,
        cast(Maliyet as double) as maliyet,
        cast(IndirimOrani as double) as indirim_orani,
        
        -- Hesaplanmış finansal / operasyonel metrikler
        cast(Miktar * BirimFiyat as double) as brut_satis_tutari,
        cast((Miktar * BirimFiyat) * (1 - IndirimOrani) as double) as net_satis_tutari,
        cast(Miktar * Maliyet as double) as toplam_maliyet,
        cast(((Miktar * BirimFiyat) * (1 - IndirimOrani)) - (Miktar * Maliyet) as double) as kar_tutari
    from raw_satis
    where SiparisID is not null
      and Tarih is not null
      and Miktar > 0
      and BirimFiyat > 0
      and Maliyet >= 0
      and IndirimOrani >= 0.0
      and IndirimOrani <= 1.0
)

select * from cleaned
