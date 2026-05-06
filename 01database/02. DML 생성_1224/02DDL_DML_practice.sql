-- DDL을 이용해서 DB만들고 테이블 만들기/삭제하기
-- Create database/schema 데이터베이스 이름;
create database sampledb2; 
create database if not exists sampledb2;
show databases;
drop database sampledb2;
create database if not exists sampledb2;
use sampledb2;
create table businesscard (
   name varchar(255) not null,
   address varchar(255) not null,
   telephone varchar(15) null);
-- 테이블 목록 조회 show tables; 
show tables;
-- 테이블의 속성, 제약조건 보기 desc 테이블명;
desc businesscard; 
-- 이미 만들어진 테이블의 속성 변경하기 alter
-- name 컬럼에 not null에서 null로 변경
alter table businesscard modify name varchar(100) null;
desc businesscard;

insert into businessscard (`name`, `address`, `telephone`)
values ('bob', '서초동 123', '02-1234-5678'),
('sam', '서초동 124', '02-1234-5679'), 
('bob2', '서초동 125', '02-1234-5680');

insert into businesscard(`address`)
values('서초동 126');
select * from businesscard;

insert into businesscard(`name`, `address`, `telephone`)
values ('bob5', '서초동 125', '02-1234-5683');

-- Primary Key Autoincrement 적용하기
alter table businesscard add column idx int not null auto_increment primary key;
desc businesscard;
select * from businesscard;
insert into businesscard(`address`, `name`, `no`, `telephone`)
values('서초동 131', 'bob7', 9, '02-1234-5685');

-- auto_increment가 설정된 컬럼이 있는 경우 반드시 컬럼명을 명시해주어야 한다. 
insert into businesscard(`address`, `name`, `no`, `telephone`)
values ('bob8', '서초동 132', 10, '02-1234-5698');

------------------------------------
-- 기존 테이블의 자료를 수정하기 update(where 조건을 반드시 주어야 한다.)
-- update 테이블명 set 컬럼1 = 값1, 컬럼2 = 값2 where 조건;
-- ---------------------------------
-- 트랜젝션 여러 dm1을 한 묶음으로 처리, 중간에 문제가 생기면
-- rollback으로 되돌리고 문제가 없으면 commit으로 확정
-- autocommit 확인/전환 1=on, 0=off
select @@autocommit;
set autocommit = 0;
select @@autocommit;
start transaction;
select * from businesscard;
update businesscard set name = 'sam2', telephone='02-1111-2222', where idx = 16;
commit; 
