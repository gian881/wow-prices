alter table "public"."item_cache" alter column "quality" set default 'normal'::public.quality;

alter table "public"."item_cache" alter column "quality" set data type public.quality using "quality"::public.quality;

alter table "public"."items" alter column "quality" set default 'normal'::public.quality;

alter table "public"."items" alter column "quality" set data type public.quality using "quality"::public.quality;


