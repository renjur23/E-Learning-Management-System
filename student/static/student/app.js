document.addEventListener('submit',function(e){const f=e.target;if(f.dataset.confirm&&!window.confirm(f.dataset.confirm)){e.preventDefault();return;}if(f.method.toLowerCase()==='post'){const b=f.querySelector('button[type="submit"]');if(b){b.dataset.label=b.dataset.label||b.textContent;b.disabled=true;b.textContent='Please wait…';}}});window.addEventListener('pageshow',()=>document.querySelectorAll('button:disabled').forEach(b=>{b.disabled=false;b.textContent=b.dataset.label||'Submit';}));
const profileMenu=document.getElementById('profile-menu');
if(profileMenu){
 document.addEventListener('click',event=>{if(!profileMenu.contains(event.target))profileMenu.open=false;});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&profileMenu.open){profileMenu.open=false;profileMenu.querySelector('summary').focus();}});
}

// The server owns the deadline; this countdown only helps students submit on time.
const testTimer=document.querySelector('[data-test-deadline]');
if(testTimer){
 const form=document.getElementById('assessment-form');
 const deadline=Date.parse(testTimer.dataset.testDeadline);
 const serverNow=Date.parse(testTimer.dataset.serverNow);
 const started=performance.now();
 const wallStarted=Date.now();
 // Use server time rather than the student's clock. Absolute elapsed time
 // catches up after background-tab throttling and computer sleep.
 const navigation=performance.getEntriesByType('navigation')[0];
 const renderDelay=navigation&&navigation.responseStart>0?Math.max(0,started-navigation.responseStart):0;
 let sent=false;
 function tick(){
  const elapsed=Math.max(performance.now()-started,Date.now()-wallStarted);
  const seconds=Math.max(0,Math.ceil((deadline-serverNow-renderDelay-elapsed)/1000));
  document.getElementById('test-countdown').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');
  testTimer.classList.toggle('timer-urgent',seconds<=60);
  // Send just before the hard server deadline to allow for request travel time.
  if(seconds<=1&&!sent){sent=true;form.requestSubmit();}
 }
 if(Number.isFinite(deadline)&&Number.isFinite(serverNow)){
  form.addEventListener('submit',()=>{sent=true;});
  tick();setInterval(tick,250);
  document.addEventListener('visibilitychange',tick);
  window.addEventListener('pageshow',tick);
  window.addEventListener('focus',tick);
 }
}

// Refresh an upcoming schedule when the shared opening time is reached.
document.querySelectorAll('[data-test-opens]').forEach(node=>{
 const opens=Date.parse(node.dataset.testOpens);
 if(Number.isFinite(opens)&&opens>Date.now()){
  const interval=setInterval(()=>{if(Date.now()>=opens){clearInterval(interval);window.location.reload();}},1000);
 }
});
