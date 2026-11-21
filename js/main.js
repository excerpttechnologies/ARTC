// Mobile menu
const mb=document.querySelector('.menu-btn'),nv=document.querySelector('.navigation');
mb&&mb.addEventListener('click',()=>nv.classList.toggle('open'));
// Banner slider (auto every 4s, arrows, dots)
const sl=document.getElementById('slider');
if(sl){const s=[...sl.querySelectorAll('.slide')],d=[...sl.querySelectorAll('.dots button')];let i=0,t;
 const go=n=>{i=(n+s.length)%s.length;s.forEach((x,k)=>x.classList.toggle('active',k===i));d.forEach((x,k)=>x.classList.toggle('on',k===i))};
 const run=()=>{clearInterval(t);t=setInterval(()=>go(i+1),4000)};
 sl.querySelector('.prev').onclick=()=>{go(i-1);run()};sl.querySelector('.next').onclick=()=>{go(i+1);run()};
 d.forEach((b,k)=>b.onclick=()=>{go(k);run()});go(0);run();}
// Contact form (front-end check; connect Formspree/EmailJS to really send)
const cf=document.getElementById('cf');
if(cf){const st=cf.querySelector('.fs');cf.addEventListener('submit',e=>{e.preventDefault();
 const ok=[...cf.querySelectorAll('[required]')].every(f=>f.value.trim()&&(f.type!=='email'||/^\S+@\S+\.\S+$/.test(f.value)));
 st.className='fs '+(ok?'ok':'err');st.textContent=ok?'Thank you! We will contact you soon.':'Please fill name, a valid email and message.';if(ok)cf.reset();});}
