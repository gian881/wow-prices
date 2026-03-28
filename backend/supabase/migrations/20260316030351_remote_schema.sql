alter table "public"."item_cache" alter column "quality" drop default;

alter table "public"."item_cache" alter column "quality" set data type public.quality using (
    case quality
        when 0 then 'normal'
        when 1 then 'tier_1'
        when 2 then 'tier_2'
        when 3 then 'tier_3'
        else 'normal'
    end
)::public.quality;

alter table "public"."item_cache" alter column "quality" set default 'normal'::public.quality;

alter table "public"."items" alter column "quality" drop default;

alter table "public"."items" alter column "quality" set data type public.quality using (
    case quality
        when 0 then 'normal'
        when 1 then 'tier_1'
        when 2 then 'tier_2'
        when 3 then 'tier_3'
        else 'normal'
    end
)::public.quality;

alter table "public"."items" alter column "quality" set default 'normal'::public.quality;
