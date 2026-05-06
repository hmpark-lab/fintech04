show databases;
use sakila;
show tables;
select * from film;
select title, release_year from film;
select title as 영화제목, rental_rate 대여요금 from film;
select * from film where rating="PG";
select * from film where rental_rate > 3;
select * from film where rental_rate >= 2 and rating="PG-13";
select * from film where rating="PG" or rating="G";
select * from film where rating <> "PG";
select * from film where rating !="PG";
select title,rental_rate, replacement_cost from film 
where replacement_cost > rental_rate;
select title,rental_rate, replacement_cost from film
where (replacement_cost - rental_rate) >=10;
select * from rental where rental_date>="2005-07-01";
select * from film where rental_rate between 2 and 4;
select * from film where rating in ("PG", "G", "PG-13");
select * from film where description like "%drama%";
select * from film where description like 'A Epic%';
select * from film where description like "%India";
select * from film where original_language_id is null;
select * from film where original_language_id is not null;
select * from film order by rental_rate desc;
select * from film order by rating asc, rental_rate desc;
select * from film order by rand() limit 10;
select * from film limit 3;
select distinct rating from film;
select count(*) as 영화수 from film; 
select avg(rental_rate) as 평균요금, max(rental_rate) as 최고요금, min(rental_rate) as 최저요금 from film;
select * from payment;
select sum(amount) 총결재금액 from payment;
select rating, count(*) as 영화수 from film group by rating having count(*);
select * from customer;
select * from rental;
select c.first_name, c.last_name, r.rental_date 
from customer c inner join rental r 
on c.customer_id = r.customer_id;
select c.customer_id, c.first_name, c.last_name, r.rental_date 
from customer c right join rental r 
on c.customer_id = r.customer_id
where r.rental_date >= '2005-07-01';
select c.customer_id, count(r.rental_id) as 대여횟수
from customer c
left join rental r on c.customer_id = r.customer_id
group by c.customer_id
having count(r.rental_id) >= 10
order by 대여횟수 desc;