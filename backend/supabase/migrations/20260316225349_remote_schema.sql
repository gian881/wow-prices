alter table "public"."settings" add column "description" text not null default ''::text;

alter table "public"."settings" add column "label" text not null default ''::text;


