CREATE TABLE "users" (
  "id" int PRIMARY KEY,
  "email" varchar UNIQUE NOT NULL,
  "first_name" varchar NOT NULL,
  "last_name" varchar NOT NULL,
  "organization" varchar NOT NULL,
  "hashed_password" varchar NOT NULL
);

CREATE TABLE "roles" (
  "id" int PRIMARY KEY,
  "name" varchar UNIQUE NOT NULL
);

CREATE TABLE "user_roles" (
  "user_id" int,
  "role_id" int,
  PRIMARY KEY ("user_id", "role_id")
);

CREATE TABLE "categories" (
  "id" int PRIMARY KEY,
  "name" varchar NOT NULL,
  "source" varchar DEFAULT 'IPTC'
);

CREATE TABLE "information_sources" (
  "id" int PRIMARY KEY,
  "name" varchar NOT NULL,
  "medium" varchar,
  "rss_url" varchar NOT NULL,
  "iptc_category" varchar
);

CREATE TABLE "rss_channels" (
  "id" int PRIMARY KEY,
  "url" varchar UNIQUE NOT NULL,
  "information_source_id" int,
  "category_id" int
);

CREATE TABLE "news_items" (
  "id" int PRIMARY KEY,
  "title" varchar NOT NULL,
  "link" varchar UNIQUE NOT NULL,
  "summary" text,
  "published" datetime,
  "channel_id" int
);

CREATE TABLE "alerts" (
  "id" int PRIMARY KEY,
  "name" varchar NOT NULL,
  "descriptors" json,
  "categories" json,
  "cron_expression" varchar,
  "is_active" boolean NOT NULL,
  "user_id" int
);

CREATE TABLE "alert_news" (
  "id" int PRIMARY KEY,
  "alert_id" int,
  "news_item_id" int
);

CREATE TABLE "notifications" (
  "id" int PRIMARY KEY,
  "timestamp" datetime,
  "metrics" json,
  "alert_id" int
);

COMMENT ON COLUMN "categories"."name" IS '17 valores IPTC';

ALTER TABLE "user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "roles" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "rss_channels" ADD FOREIGN KEY ("information_source_id") REFERENCES "information_sources" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "rss_channels" ADD FOREIGN KEY ("category_id") REFERENCES "categories" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "news_items" ADD FOREIGN KEY ("channel_id") REFERENCES "rss_channels" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "alerts" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "alert_news" ADD FOREIGN KEY ("alert_id") REFERENCES "alerts" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "alert_news" ADD FOREIGN KEY ("news_item_id") REFERENCES "news_items" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "notifications" ADD FOREIGN KEY ("alert_id") REFERENCES "alerts" ("id") DEFERRABLE INITIALLY IMMEDIATE;
