drop table if exists items;
create table items (
    id integer primary key,
    img_url text not null,
    name text not null,
    base_cost integer,
    full_cost integer
);

drop table if exists matches;
create table matches (
    id integer primary key,
    time_stamp datetime not null,
    item_sets text not null,
    participants text not null,
    participantIds text not null,
    teams text not null,
    game_number int not null,
    region_id int not null
);

drop table if exists champions;
create table champions (
    id integer primary key,
    img_url text not null
);