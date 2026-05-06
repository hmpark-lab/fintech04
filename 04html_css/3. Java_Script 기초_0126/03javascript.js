// html에서 id가 title인 태그를 찾아서 웹브라우저 console에 결과 출력
 const title = document.querySelector("#title")
console.log(title)

//링크 클릭 이벤트 연결하기 a태그를 찾아서 클릭시 "링크를 클릭했습니다."
const link = document.querySelector("a")
link.addEventListener("click", ()=> {
    console.log("링크를 클릭했습니다.");
});
// HTML 요소에 마우스 이벤트 연결하기
const box = document.querySelector('#box')
box.addEventListener("mouseenter", ()=> {
    box.style.backgroundColor = "hotpink"
});

box.addEventListener('mouseleave', ()=>{
    box.style.backgroundColor = 'aqua';
});

//클릭 이벤트 발생할 때 숫자 증가, 감소하기
const btnPlus = document.querySelector(".btnPlus");
const btnMinus = document.querySelector(".btnMinus");
let num = 0; //제어할 숫자값을 0으로 초기화

//btnPlus를 클릭할 때
btnPlus.addEventListener("click", e=>{
    e.preventDefault();
    num++; // num값을 1씩 증가
    console.log(num);
});

//btnMinus를 클릭할 때
btnMinus.addEventListener("click", e=>{
    e.preventDefault();
    num--; // num값을 1씩 감소
    console.log(num);
});

//버튼을 클릭하면 좌우로 회전하는 박스 만들기
const btnleft = document.querySelector(".btnLeft");
const btnRight = document.querySelector(".btnRight");
const box2 = document.querySelector('#box2');
const deg = 45; 
let num2 = 0; 

//btnLeft를 클릭할 때
btnleft.addEventListener("click", e=>{
    e.preventDefault();
    num2--;
    console.log(`btnLeft를 클릭했을 때 num2에 있는 값: ${num2}`);
    box2.style.transform = `rotate(${num2 * deg}deg)`;
});

//btnRight를 클릭할 때
btnleft.addEventListener("click", e=>{
    e.preventDefault();
    num2++;
    console.log(`btnLeft를 클릭했을 때 num2에 있는 값: ${num2}`);
    box2.style.transform = `rotate(${num2 * deg}deg)`;
});