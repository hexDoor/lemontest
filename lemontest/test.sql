create view test1
as
select 'asdf?'
;

create or replace function
   test2(t text)
      returns text
as $$
   select 'wrong'
$$ language sql;