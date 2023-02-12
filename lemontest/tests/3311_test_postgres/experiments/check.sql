-- COMP3311 22T3 Assignment 2
--
-- check.sql ... checking functions
--
-- Written by: John Shepherd, September 2012
-- Updated by: John Shepherd, October 2022
--

--
-- Helper functions
--

create or replace function
        ass1_table_exists(tname text) returns boolean
as $$
declare
        _check integer := 0;
begin
        select count(*) into _check from pg_class
        where relname=tname and relkind='r';
        return (_check = 1);
end;
$$ language plpgsql;

create or replace function
        ass1_view_exists(tname text) returns boolean
as $$
declare
        _check integer := 0;
begin
        select count(*) into _check from pg_class
        where relname=tname and relkind='v';
        return (_check = 1);
end;
$$ language plpgsql;

create or replace function
        ass1_function_exists(tname text) returns boolean
as $$
declare
        _check integer := 0;
begin
        select count(*) into _check from pg_proc
        where proname=tname;
        return (_check > 0);
end;
$$ language plpgsql;

-- ass1_check_result:
-- * determines appropriate message, based on count of
--   excess and missing tuples in user output vs expected output

create or replace function
        ass1_check_result(nexcess integer, nmissing integer) returns text
as $$
begin
        if (nexcess = 0 and nmissing = 0) then
                return 'correct';
        elsif (nexcess > 0 and nmissing = 0) then
                return 'too many result tuples';
        elsif (nexcess = 0 and nmissing > 0) then
                return 'missing result tuples';
        elsif (nexcess > 0 and nmissing > 0) then
                return 'incorrect result tuples';
        end if;
end;
$$ language plpgsql;

-- ass1_check:
-- * compares output of user view/function against expected output
-- * returns string (text message) containing analysis of results

create or replace function
        ass1_check(_type text, _name text, _res text, _query text) returns text
as $$
declare
        nexcess integer;
        nmissing integer;
        excessQ text;
        missingQ text;
begin
        if (_type = 'view' and not ass1_view_exists(_name)) then
                return 'No '||_name||' view; did it load correctly?';
        elsif (_type = 'function' and not ass1_function_exists(_name)) then
                return 'No '||_name||' function; did it load correctly?';
        elsif (not ass1_table_exists(_res)) then
                return _res||': No expected results!';
        else
                excessQ := 'select count(*) '||
                           'from (('||_query||') except '||
                           '(select * from '||_res||')) as X';
                -- raise notice 'Q: %',excessQ;
                execute excessQ into nexcess;
                missingQ := 'select count(*) '||
                            'from ((select * from '||_res||') '||
                            'except ('||_query||')) as X';
                -- raise notice 'Q: %',missingQ;
                execute missingQ into nmissing;
                return ass1_check_result(nexcess,nmissing);
        end if;
        return '???';
end;
$$ language plpgsql;

-- ass1_rescheck:
-- * compares output of user function against expected result
-- * returns string (text message) containing analysis of results

create or replace function
        ass1_rescheck(_type text, _name text, _res text, _query text) returns text
as $$
declare
        _sql text;
        _chk boolean;
begin
        if (_type = 'function' and not ass1_function_exists(_name)) then
                return 'No '||_name||' function; did it load correctly?';
        elsif (_res is null) then
                _sql := 'select ('||_query||') is null';
                -- raise notice 'SQL: %',_sql;
                execute _sql into _chk;
                -- raise notice 'CHK: %',_chk;
        else
                _sql := 'select ('||_query||') = '||quote_literal(_res);
                -- raise notice 'SQL: %',_sql;
                execute _sql into _chk;
                -- raise notice 'CHK: %',_chk;
        end if;
        if (_chk) then
                return 'correct';
        else
                return 'incorrect result';
        end if;
end;
$$ language plpgsql;

-- check_all:
-- * run all of the checks and return a table of results

drop type if exists TestingResult cascade;
create type TestingResult as (test text, result text);

create or replace function
        check_all() returns setof TestingResult
as $$
declare
        i int;
        testQ text;
        result text;
        out TestingResult;
        tests text[] := array[
                                'q1', 'q2', 'q3', 'q4', 'q5',
                                'q6', 'q7', 'q8', 'q9', 'q10',
                                'q11a', 'q11b', 'q11c', 'q11d', 'q11e', 'q11f',
                                'q12a', 'q12b', 'q12c', 'q12d', 'q12e', 'q12f', 'q12g'
                                ];
begin
        for i in array_lower(tests,1) .. array_upper(tests,1)
        loop
                testQ := 'select check_'||tests[i]||'()';
                execute testQ into result;
                out := (tests[i],result);
                return next out;
        end loop;
        return;
end;
$$ language plpgsql;


--
-- Test Cases
--

-- Q1 --

create or replace function check_q1() returns text
as $chk$
select ass1_check('view','q1','q1_expected',
                   $$select * from q1$$)
$chk$ language sql;

drop table if exists q1_expected;
create table q1_expected (
    brewery text,
    suburb text
);

COPY q1_expected (brewery, suburb) FROM stdin;
Algorithm Brewing       Marrickville
Bracket Brewing Alexandria
Malt Wolf Pty Ltd       \N
Slow Lane Brewing       Botany
The Bondi Brewing Co    Bondi
White Bay Beer Co       Rozelle
\.

-- Q2 --

create or replace function check_q2() returns text
as $chk$
select ass1_check('view','q2','q2_expected',
                   $$select * from q2$$)
$chk$ language sql;

drop table if exists q2_expected;
create table q2_expected (
    beer text,
    brewery text
);

COPY q2_expected (beer, brewery) FROM stdin;
Barley Wine     Hawkers Beer
Double Red IPA  Mountain Culture Beer Co
Hazy IPA        Gwei Lo Beer
Hazy IPA        Hawkers Beer
Hazy IPA        Holgate Brewhouse
Hazy IPA        Malt Wolf Pty Ltd
Hazy IPA        One Drop Brewing Co.
IPA     AleSmith Brewing Co
IPA     Detour Beer Co
IPA     Zytho Brewing
Imperial IPA    Hawkers Beer
Imperial Red Ale        Hope Brewery
Imperial Stout  Ekim Brewing Co
Imperial Stout  Mountain Goat Beer
Lager   Balter Brewing Co
Lager   Mountain Culture Beer Co
Oatmeal Stout   Ocean Reach Brewing
Pale Ale        Algorithm Brewing
Pale Ale        East Sydney Brewing
Pale Ale        Mountain Culture Beer Co
Pale Ale        Prancing Pony Brewery
Pale Ale        Sierra Nevada Brewing Company
Porter  Colonial Brewing Company
Red IPA Bulli Brewing Co
Russian Imperial Stout  Bracket Brewing
Saison  Exit Brewing
Scotch Ale      Caledonian Brewery
West Coast IPA  Bracket Brewing
West Coast IPA  Mr.Banks Brewing Co
\.


-- Q3 --

create or replace function check_q3() returns text
as $chk$
select ass1_check('view','q3','q3_expected',
                   $$select * from q3$$)
$chk$ language sql;

drop table if exists q3_expected;
create table q3_expected (
    brewery text,
    founded YearValue
);

COPY q3_expected (brewery, founded) FROM stdin;
Sierra Nevada Brewing Company   1980
\.


-- Q4 --

create or replace function check_q4() returns text
as $chk$
select ass1_check('view','q4','q4_expected',
                   $$select * from q4$$)
$chk$ language sql;

drop table if exists q4_expected;
create table q4_expected (
    style text,
    count integer
);

COPY q4_expected (style, count) FROM stdin;
Amber IPA       1
American IPA    1
Australian IPA  1
Black Double IPA        1
Black IPA       3
Black Imperial IPA      1
Brown IPA       1
Brut IPA        1
Creamy IPA      1
Cryo IPA        1
Dark IPA        2
Double IPA      43
Double NEIPA    11
Double Oat Cream IPA    1
Double Red IPA  6
Dry Hazy IPA    1
Extra IPA       1
Hazy Double IPA 20
Hazy IPA        72
Hazy Imperial IPA       1
Hazy Triple IPA 6
IPA     102
Ice Cream Cake IPA      1
Imperial Hazy IPA       2
Imperial IPA    17
Imperial NEIPA  1
Imperial Red IPA        7
Imperial Thickshake IPA 1
Kettle soured Double IPA        1
Milkshake IPA   4
NEIPA   49
New World IPA   1
Oat Cream IPA   17
Oat Cream NEIPA 2
Quintuple IPA   1
Red Double IPA  1
Red IPA 15
Red Rye IPA     1
Rye IPA 1
Session Hazy IPA        1
Session IPA     2
Sour Hazy IPA   1
Sour Red IPA    1
Triple IPA      6
Triple NEIPA    1
Tropical Brut IPA       1
Vermont IPA     1
West Coast IPA  18
White IPA       1
\.


-- Q5 --

create or replace function check_q5() returns text
as $chk$
select ass1_check('view','q5','q5_expected',
                   $$select * from q5$$)
$chk$ language sql;

drop table if exists q5_expected;
create table q5_expected (
    brewery text,
    location text
);

COPY q5_expected (brewery,location) FROM stdin;
AleSmith Brewing Co     San Diego
Almanac Beer Company    Alameda
Alpine Beer Company     Alpine
Anderson Valley Brewing Company Boonville
Ballast Point Brewing Co        San Diego
Bear Republic Brewing   Cloverdale
Belching Beaver Brewery Oceanside
Cellarmaker Brewing Co  San Francisco
Figueroa Mountain Brewing Co    Buellton
Firestone Walker Brewing Company        Paso Robles
Golden Road Brewing     Los Angeles
Heretic Brewing Fairfeld
High Water Brewing Inc  Lodi
Humble Sea Brewing      Santa Cruz
Karl Strauss Brewing Company    San Diego
Knee Deep Brewing Co    Auburn
Local Brewing Co        San Francisco
Modern Times Beer       Point Loma
Monkish Brewing Company Torrance
Moonraker Brewing       Auburn
Mother Earth Brew Company       Vista
Northcoast Brewing Co   Fort Bragg
Offshoot Beer   Placentia
Pizza Port Brewing Company      Carlsbad
Sierra Nevada Brewing Company   Chico
Smog City Brewing Co    Torrance
Societe Brewing Company Kearny Mesa
Stone Brewing   Escondido
The Bruery      Placentia
\.


-- Q6 --

create or replace function check_q6() returns text
as $chk$
select ass1_check('view','q6','q6_expected',
                   $$select * from q6$$)
$chk$ language sql;

drop table if exists q6_expected;
create table q6_expected (
    beer text,
    brewery text,
        abv ABVvalue
);

COPY q6_expected (beer,brewery,abv) FROM stdin;
Jumping the Shark 2015  Moon Dog Craft Brewery  18.4
\.


-- Q7 --

create or replace function check_q7() returns text
as $chk$
select ass1_check('view','q7','q7_expected',
                   $$select * from q7$$)
$chk$ language sql;

drop table if exists q7_expected;
create table q7_expected (
    hop text
);

COPY q7_expected (hop) FROM stdin;
Citra
\.


-- Q8 --

create or replace function check_q8() returns text
as $chk$
select ass1_check('view','q8','q8_expected',
                   $$select * from q8$$)
$chk$ language sql;

drop table if exists q8_expected;
create table q8_expected (
    brewery text
);

COPY q8_expected (brewery) FROM stdin;
Abbaye de Scourmont - Chimay
Aegir Bryggeri
Algorithm Brewing
Almanac Beer Company
Alpine Beer Company
Bayerische Staatsbrauerei Weihenstephan
Birra del Borgo
Brasserie Dupont
Brasserie d'Orval
Brasserie de Rochefort
Brauerei Heller
Brauerei Schloss Eggenberg
Brouwerij Huyghe
Brouwerij Verhaeghe
Caledonian Brewery
Capital Brewing Co
Carbon Brews
Coopers Brewery
Counter Culture Brewing
Darkes Cider
Dogfish Head Brewery
East Sydney Brewing
Future Mountain Brewing and Blending
Great Leap Brewing
Hair of the Dog Brewing Company
Harviestoun Brewery
Hemingway's Brewing
Heroes Beer Co
Kereru Brewing Co
Lervig Aktiebryggeri
Malt Shovel Brewers
Mornington Peninsula Brewery
Nogne 0 (Hansa Borg)
Oriental Brewery
Pelican Brewing
Rodenbach Brewery
Sail and Anchor Brewing Co
Samuel Smiths Brewery
Slow Lane Brewing
Spencer Brewery
To Ol
Two Birds Brewing
Urban Alley Brewery
Wildflower Brewing and Blending
Willie Smiths Cidery
Young Master Hong Kong
\.


-- Q9 --

create or replace function check_q9() returns text
as $chk$
select ass1_check('view','q9','q9_expected',
                   $$select * from q9$$)
$chk$ language sql;

drop table if exists q9_expected;
create table q9_expected (
    grain text
);

COPY q9_expected (grain) FROM stdin;
Oats
\.

-- Q10 --

create or replace function check_q10() returns text
as $chk$
select ass1_check('view','q10','q10_expected',
                   $$select * from q10$$)
$chk$ language sql;

drop table if exists q10_expected;
create table q10_expected (
    unused text
);

COPY q10_expected (unused) FROM stdin;
Acai
\.


-- Q11 --

create or replace function check_q11a() returns text
as $chk$
select ass1_check('function','q11','q11a_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('Australia')$$)
$chk$ language sql;

drop table if exists q11a_expected;
create table q11a_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11a_expected (minabv,maxabv) FROM stdin;
0       18.4
\.

create or replace function check_q11b() returns text
as $chk$
select ass1_check('function','q11','q11b_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('australia')$$)
$chk$ language sql;

drop table if exists q11b_expected;
create table q11b_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11b_expected (minabv,maxabv) FROM stdin;
0       0
\.

create or replace function check_q11c() returns text
as $chk$
select ass1_check('function','q11','q11c_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('United States')$$)
$chk$ language sql;

drop table if exists q11c_expected;
create table q11c_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11c_expected (minabv,maxabv) FROM stdin;
4       15.5
\.

create or replace function check_q11d() returns text
as $chk$
select ass1_check('function','q11','q11d_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('Scotland')$$)
$chk$ language sql;

drop table if exists q11d_expected;
create table q11d_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11d_expected (minabv,maxabv) FROM stdin;
4.5     55
\.

create or replace function check_q11e() returns text
as $chk$
select ass1_check('function','q11','q11e_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('No such place')$$)
$chk$ language sql;

drop table if exists q11e_expected;
create table q11e_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11e_expected (minabv,maxabv) FROM stdin;
0       0
\.

create or replace function check_q11f() returns text
as $chk$
select ass1_check('function','q11','q11f_expected',
                   $$select minabv::numeric(4,1),maxabv::numeric(4,1) from q11('USA')$$)
$chk$ language sql;

drop table if exists q11f_expected;
create table q11f_expected (
    minabv ABVvalue,
    maxabv ABVvalue
);

COPY q11f_expected (minabv,maxabv) FROM stdin;
0       0
\.


-- Q12 --

create or replace function check_q12a() returns text
as $chk$
select ass1_check('function','q12','q12a_expected',
                   $$select * from q12('oat cream')$$)
$chk$ language sql;

drop table if exists q12a_expected;
create table q12a_expected (
    beer text,
    brewer text,
    info text
);

COPY q12a_expected (beer,brewer,info) FROM stdin;
Oat Cream       Six String Brewing Company      \N
Oat Cream India Pale Ale        Grassy Knoll Brewing    Hops: Citra,Strata\nGrain: Oats,Pale malt,Wheat
Mango Oat Cream N.O.M.A.D Brewing       \N
DDH MBC Oat Cream IPA   Otherside Brewing Co    Hops: Bravo,Centennial,Mosaic\nGrain: Oats,Pale,Rye,Treticale,Wheat\nExtras: Lactose,Vanilla
\.

create or replace function check_q12b() returns text
as $chk$
select ass1_check('function','q12','q12b_expected',
                   $$select * from q12('imperial stout')$$)
$chk$ language sql;

drop table if exists q12b_expected;
create table q12b_expected (
    beer text,
    brewer text,
    info text
);

COPY q12b_expected (beer,brewer,info) FROM stdin;
Gulden Draak Imperial Stout     Brouwerij Van Steenberge        \N
Imperial Stout  Ekim Brewing Co \N
Imperial Stout  Mountain Goat Beer      \N
Russian Imperial Stout  Bracket Brewing \N
\.

create or replace function check_q12c() returns text
as $chk$
select ass1_check('function','q12','q12c_expected',
                   $$select * from q12('pastry stout')$$)
$chk$ language sql;

drop table if exists q12c_expected;
create table q12c_expected (
    beer text,
    brewer text,
    info text
);

COPY q12c_expected (beer,brewer,info) FROM stdin;
Banana Pastry Stout     Hop Nation Brewing Co   Extras: Banana
Peanut Butter Pastry Stout      Hop Nation Brewing Co   Extras: Peanut butter
\.

create or replace function check_q12d() returns text
as $chk$
select ass1_check('function','q12','q12d_expected',
                   $$select * from q12('Hazy IPA')$$)
$chk$ language sql;

drop table if exists q12d_expected;
create table q12d_expected (
    beer text,
    brewer text,
    info text
);

COPY q12d_expected (beer,brewer,info) FROM stdin;
Del Mar Pink Grapefruit Hazy IPA        Urbanaut Brewing Co     \N
East Coast Hazy IPA     Bracket Brewing Hops: Citra,Mosaic,Trident
Hazy IPA        Bracket Brewing Hops: Mosaic,Motueka,Nelson sauvin
Hazy IPA        Gwei Lo Beer    \N
Hazy IPA        Hawkers Beer    \N
Hazy IPA        Holgate Brewhouse       Hops: Amarillo,Azacca,Mosaic
Hazy IPA        Malt Wolf Pty Ltd       \N
Hazy IPA        Nogne 0 (Hansa Borg)    \N
Hazy IPA        One Drop Brewing Co.    Hops: Nelson sauvin,Sabro,Vic-secret\nGrain: Oat,Wheat
Mango Hazy IPA  Seventh Day Brewery     Extras: Mango
\.

create or replace function check_q12e() returns text
as $chk$
select ass1_check('function','q12','q12e_expected',
                   $$select * from q12('aquarius')$$)
$chk$ language sql;

drop table if exists q12e_expected;
create table q12e_expected (
    beer text,
    brewer text,
    info text
);

COPY q12e_expected (beer,brewer,info) FROM stdin;
Age of Aquarius Garage Project + Modern Times Beer      \N
\.

create or replace function check_q12f() returns text
as $chk$
select ass1_check('function','q12','q12f_expected',
                   $$select * from q12('omnibus')$$)
$chk$ language sql;

drop table if exists q12f_expected;
create table q12f_expected (
    beer text,
    brewer text,
    info text
);

COPY q12f_expected (beer,brewer,info) FROM stdin;
Cosmic Omnibus  AleSmith Brewing Co + Modern Times Beer Extras: Citrus zest
\.

create or replace function check_q12g() returns text
as $chk$
select ass1_check('function','q12','q12g_expected',
                   $$select * from q12('No such beer')$$)
$chk$ language sql;

drop table if exists q12g_expected;
create table q12g_expected (
    beer text,
    brewer text,
    info text
);

COPY q12g_expected (beer,brewer,info) FROM stdin;
\.