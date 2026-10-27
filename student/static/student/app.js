document.addEventListener('submit',function(e){const f=e.target;if(f.dataset.confirm&&!window.confirm(f.dataset.confirm)){e.preventDefault();return;}if(f.method.toLowerCase()==='post'){const b=f.querySelector('button[type="submit"]');if(b){b.dataset.label=b.dataset.label||b.textContent;b.disabled=true;b.textContent='Please wait…';}}});window.addEventListener('pageshow',()=>document.querySelectorAll('button:disabled').forEach(b=>{b.disabled=false;b.textContent=b.dataset.label||'Submit';}));
const profileMenu=document.getElementById('profile-menu');
if(profileMenu){
 document.addEventListener('click',event=>{if(!profileMenu.contains(event.target))profileMenu.open=false;});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&profileMenu.open){profileMenu.open=false;profileMenu.querySelector('summary').focus();}});
}
