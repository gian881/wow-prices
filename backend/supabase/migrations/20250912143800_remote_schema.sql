drop extension if exists "pg_net";

create type "public"."intent" as enum ('buy', 'sell', 'both');

create type "public"."notification_type" as enum ('price_above_alert', 'price_below_alert', 'price_below_best_avg_alert', 'price_above_best_avg_alert');

create type "public"."rarity" as enum ('POOR', 'COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY', 'ARTIFACT', 'HEIRLOOM');

create sequence "public"."notifications_id_seq";


  create table "public"."item_cache" (
    "item_id" integer not null,
    "name" text,
    "blizzard_image_url" text,
    "quality" smallint default '0'::bigint,
    "rarity" rarity default 'COMMON'::rarity
      );



  create table "public"."items" (
    "id" integer not null,
    "name" text,
    "image_path" text,
    "quality" smallint default '0'::smallint,
    "rarity" rarity default 'COMMON'::rarity,
    "quantity_threshold" integer default 100,
    "above_alert" bigint default '0'::bigint,
    "below_alert" bigint default '0'::bigint,
    "notify_sell" boolean default false,
    "notify_buy" boolean default false,
    "intent" intent default 'sell'::intent
      );



  create table "public"."notifications" (
    "id" integer not null default nextval('notifications_id_seq'::regclass),
    "type" notification_type,
    "price_diff" numeric default '0'::numeric,
    "current_price" bigint,
    "price_threshold" bigint,
    "item_id" integer,
    "read" boolean default false,
    "created_at" timestamp without time zone default CURRENT_TIMESTAMP
      );



  create table "public"."price_history" (
    "item_id" integer not null,
    "price" bigint,
    "quantity" integer default 0,
    "timestamp" timestamp without time zone default CURRENT_TIMESTAMP
      );


alter sequence "public"."notifications_id_seq" owned by "public"."notifications"."id";

CREATE UNIQUE INDEX idx_16395_sqlite_autoindex_items_1 ON public.items USING btree (id);

CREATE UNIQUE INDEX idx_16416_item_cache_pkey ON public.item_cache USING btree (item_id);

CREATE UNIQUE INDEX notifications_pkey ON public.notifications USING btree (id);

alter table "public"."item_cache" add constraint "idx_16416_item_cache_pkey" PRIMARY KEY using index "idx_16416_item_cache_pkey";

alter table "public"."items" add constraint "idx_16395_sqlite_autoindex_items_1" PRIMARY KEY using index "idx_16395_sqlite_autoindex_items_1";

alter table "public"."notifications" add constraint "notifications_pkey" PRIMARY KEY using index "notifications_pkey";

alter table "public"."notifications" add constraint "notifications_item_id_fkey" FOREIGN KEY (item_id) REFERENCES items(id) not valid;

alter table "public"."notifications" validate constraint "notifications_item_id_fkey";

alter table "public"."price_history" add constraint "price_history_item_id_fkey" FOREIGN KEY (item_id) REFERENCES items(id) not valid;

alter table "public"."price_history" validate constraint "price_history_item_id_fkey";


