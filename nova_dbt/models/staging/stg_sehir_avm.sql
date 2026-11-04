with source as (
    select * from {{ ref('sehir_avm') }}
),

renamed as (
    select
        lower(trim(sehir)) as sehir,
        lower(trim(bolge)) as bolge,
        cast(avm_sayisi as integer) as avm_sayisi,
        cast(nufus_tahmini as bigint) as nufus_tahmini
    from source
)

select * from renamed
