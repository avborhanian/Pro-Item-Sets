drop table if exists items;
create table items (
    id integer primary key,
    img_url text not null,
    name text not null,
    base_cost integer,
    full_cost integer
);

drop table if exists leagues;
create table leagues (
    id int primary key,
    name text not null,
    acronym text
);

drop table if exists summoners;
create table summoners (
    id int primary key,
    name text not null,
    img_url text not null
);

drop table if exists match_details;
create table match_details (
    series_id integer primary key,
    region_id int not null,
    team_one_id text not null,
    team_two_id text not null,
    league_week text not null
);

drop table if exists matches;
create table matches (
    match_id integer primary key,
    time_stamp datetime not null,
    game_number int not null,
    series_id int not null,
    winning_team_id int not null
);

drop table if exists teams;
create table teams (
    team_id integer primary key,
    team_name text not null,
    logo_url text not null,
    acronym text
);

drop table if exists match_participant;
create table match_participant (
    match_id integer not null,
    player_id integer not null,
    participant_id integer not null,
    team_id integer not null,
    kills integer not null,
    deaths integer not null,
    assists integer not null,
    champion integer not null,
    spell_id_one integer not null,
    spell_id_two integer not null,
    item_set text not null
);

drop table if exists playerinfo;
create table playerinfo (
    player_id integer primary key,
    name text not null,
    photo_url text not null
);

drop table if exists champions;
create table champions (
    id integer primary key,
    img_url text not null
);