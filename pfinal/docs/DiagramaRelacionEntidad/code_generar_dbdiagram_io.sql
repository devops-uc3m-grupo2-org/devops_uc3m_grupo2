Table users {
id int [pk]
email varchar [unique, not null]
first_name varchar [not null]
last_name varchar [not null]
organization varchar [not null]
hashed_password varchar [not null]
}

Table roles {
id int [pk]
name varchar [unique, not null]
}

Table user_roles {
user_id int [pk, ref: > users.id]
role_id int [pk, ref: > roles.id]
}

Table categories {
id int [pk]
name varchar [not null, note: "17 valores IPTC"]
source varchar [default: "IPTC"]
}

Table information_sources {
id int [pk]
name varchar [not null]
medium varchar
rss_url varchar [not null]
iptc_category varchar
}

Table rss_channels {
id int [pk]
url varchar [unique, not null]
information_source_id int [ref: > information_sources.id]
category_id int [ref: > categories.id]
}

Table news_items {
id int [pk]
title varchar [not null]
link varchar [unique, not null]
summary text
published datetime
channel_id int [ref: > rss_channels.id]
}

Table alerts {
id int [pk]
name varchar [not null]
descriptors json
categories json
cron_expression varchar
is_active boolean [not null]
user_id int [ref: > users.id]
}

Table alert_news {
id int [pk]
alert_id int [ref: > alerts.id]
news_item_id int [ref: > news_items.id]
}

Table notifications {
id int [pk]
timestamp datetime
metrics json
alert_id int [ref: > alerts.id]
}
