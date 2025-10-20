const params=new URLSearchParams(location.search);
const roomId=params.get('room_id');
const token=localStorage.getItem('token');
const name=localStorage.getItem('user_name')||'anon';
if(!token||!roomId) location.href='/static/join.html';

const socket=io({path:'/socket.io',auth:{token},transports:['websocket','polling']});
const $status=document.getElementById('status');
const $messages=document.getElementById('messages');
const $input=document.getElementById('m');
const $send=document.getElementById('send');
const $file=document.getElementById('file');
const $upload=document.getElementById('btn-upload');
const $typing=document.getElementById('typing');

function addLine(html){const li=document.createElement('li');li.innerHTML=html;$messages.appendChild(li);$messages.scrollTop=$messages.scrollHeight;}

socket.on('connect',()=>{$status.textContent='Connected ✔'; socket.emit('set_profile',{name}); socket.emit('join_room',{room_id:roomId});});
socket.on('user_joined',d=>addLine(`🔔 <b>${escapeHtml(d.username)}</b> joined`));
socket.on('user_left',d=>addLine(`🔕 <b>${escapeHtml(d.username)}</b> left`));
socket.on('typing',d=>{ $typing.textContent=`${d.username} is typing...`; clearTimeout(window._t); window._t=setTimeout(()=>($typing.textContent=''),600);});
socket.on('chat_message',m=>{if(m.room_id!==roomId) return; const t=new Date(m.created_at).toLocaleTimeString(); addLine(`[${t}] <b>${escapeHtml(m.username)}</b>: ${escapeHtml(m.text)}`)});
socket.on('file_uploaded',a=>{if(a.room_id!==roomId) return; const t=new Date(a.created_at).toLocaleTimeString(); const isImg=a.mime_type&&a.mime_type.startsWith('image/'); const pv=isImg?`<div class="thumb"><img src="${a.url}"/></div>`:'📎'; addLine(`[${t}] <b>${escapeHtml(a.username)}</b> uploaded: ${pv} <a href="${a.url}" download>${escapeHtml(a.original_name)}</a>`)});

$send.onclick=async()=>{const text=$input.value.trim(); if(!text) return; await fetch('/chat/message',{method:'POST',headers:{Authorization:'Bearer '+token},body:new URLSearchParams({room_id:roomId,text})}); $input.value='';};
$input.addEventListener('input',()=>socket.emit('typing',{room_id:roomId}));

$upload.onclick=async()=>{const fs=$file.files; if(!fs||!fs.length) return; const fd=new FormData(); for(const f of fs) fd.append('files',f); fd.append('room_id',roomId); const res=await fetch('/chat/upload',{method:'POST',headers:{Authorization:'Bearer '+token},body:fd}); if(!res.ok) alert(await res.text()); else $file.value='';};

// load history
(async()=>{const qs=new URLSearchParams({room_id:roomId,limit:'50'}).toString(); const msgs=await (await fetch('/chat/messages?'+qs)).json(); msgs.forEach(m=>{const t=new Date(m.created_at).toLocaleTimeString(); addLine(`[${t}] <b>${escapeHtml(m.username)}</b>: ${escapeHtml(m.text)}`)}); const files=await (await fetch('/chat/attachments?'+qs)).json(); files.forEach(a=>{const t=new Date(a.created_at).toLocaleTimeString(); const isImg=a.mime_type&&a.mime_type.startsWith('image/'); const pv=isImg?`<div class="thumb"><img src="${a.url}"/></div>`:'📎'; addLine(`[${t}] <b>${escapeHtml(a.username)}</b> uploaded: ${pv} <a href="${a.url}" download>${escapeHtml(a.original_name)}</a>`)});})();

function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}