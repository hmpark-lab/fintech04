create database Learn_system;
use learn_system;
create table student(
student_id int primary key,
student_name varchar(8),
height int,
department_id int
);
create table department(
department_id int,
department_name varchar(20)
);
create table professor(
professor_id int,
professor_name varchar(10),
department_id int
);
create table course(
course_id int,
course_name varchar(10),
professor_id int,
start_date date,
end_date date
);
create table student_course(
student_id int,
course_id int
);

insert into department values(1, '수학');
insert into department values(2, '국문학');
insert into department values(3, '정보통신공학');
insert into department values(4, '모바일공학');

desc department;
select * from department;

insert into student values(1, '가길동', 177, 1);
insert into student values(2, '나길동', 178, 1);
insert into student values(3, '다길동', 179, 1);
insert into student values(4, '라길동', 180, 2);
insert into student values(5, '마길동', 170, 2);
insert into student values(6, '바길동', 172, 3);
insert into student values(7, '사길동', 166, 4);
insert into student values(8, '아길동', 192, 4);

desc student;
select * from student;

insert into professor values(1, '가교수',1);
insert into professor values(2, '나교수',2);
insert into professor values(3, '다교수',3);
insert into professor values(4, '빌게이츠' ,4);
insert into professor values(5, '스티브잡스',3);

desc professor;
select * from professor;

insert into course values(1, '교양영이', 1, '2016/9/2', '2016/11/30');
insert into course values(2, '데이터베이스 입문', 3, '2016/8/20','2016/10/30');
insert into course values(3, '회로이론', 2, '2016/10/20', '2016/12/30');
insert into course values(4, '공업수학', 4,'2016/11/2', '2017/1/28');
insert into course values(5, '객체지향프로그래밍', 3, '2016/11/1', '2017/1/30');

desc course;
select * from course;

insert into student_course values(1, 1);
insert into student_course values(2, 1);
insert into student_course values(3, 2);
insert into student_course values(4, 3);
insert into student_course values(5, 4);
insert into student_course values(6, 5);
insert into student_course values(7, 5);

desc student_course;
select * from student_course;

-- Q1.
select s.student_id, s.student_name, s.height, d.department_id, d.department_name from department d inner join student s on s.department_id = d.department_id;
-- Q2. 
select professor_id from professor where professor_name = '가교수';
-- Q3. 
select d.department_name, count(p.professor_id) from professor p inner join department d on d.department_id=p.department_id group by d.department_name;
-- Q4.
select s.student_id, s.student_name,s.height, s.department_id, d.department_name from department d inner join student s on s.department_id=d.department_id where department_name='정보통신공학';

-- Q5. 
select p.professor_id, p.professor_name, d.department_id, d.department_name from professor p join department d  on d.department_id=p.department_id 
where department_name='정보통신공학';
-- Q6. 
select student_name, department_name from student s join department d on s.department_id=d.department_id where s.student_name like '아%';
-- Q7.
select count(student_id) from student where height between 180 and 190;
-- Q8.
select d.department_name, max(s.height), avg(s.height) from student s join department d group by d.department_name;
-- Q9.
select student_name from student where department_id=(select department_id from student where student_name = '다길동');
-- Q10.
select s.student_name, c.course_name from student s join student_course sc on s.student_id=sc.student_id join course c on c.course_id=sc.course_id where c.start_date like '2016-11%';
-- Q11.
select s.student_name from student s join student_course sc on s.student_id=sc.student_id join course c on c.course_id=sc.student_id where c.course_name = '데이터베이스 입문';
-- Q12.
select count(s.student_id) from student s 
join professor p on p.department_id=s.department_id 
join course c on c.professor_id=p.professor_id 
where p.professor_name='빌게이츠';

select count(s.student_id) from student s 
join student_course sc on sc.student_id=s.student_id
where course_id=(select course_id from professor p join course c on c.professor_id=p.professor_id
where p.professor_name='빌게이츠');

select count(s.student_id) from student s
join student_course sc on s.student_id=sc.student_id
where course_id = (select course_id from course c join professor p on p.professor_id=c.professor_id where professor_name = '빌게이츠');


select * from student;
select * from professor;
select * from course;
select * from student_course;