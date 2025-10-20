const token=localStorage.getItem('token');
if(!token) location.href='/static/login.html';
const $country=document.getElementById('country');
const $room=document.getElementById('room');
const $newroom=document.getElementById('newroom');
const $status=document.getElementById('status');

async function getJSON(url){
  const res=await fetch(url);
  const data=await res.json();
  if(!res.ok) throw new Error(data.detail||'error');
  return data;
}

(async()=>{
  const countries=await getJSON('/rooms/countries');
  $country.innerHTML=countries.map(c=>`<option value="${c.code}">${c.name}</option>`).join('');
  await refreshRooms();
})();

$country.onchange=refreshRooms;
async function refreshRooms(){
  const code=$country.value; if(!code) return;
  const rooms=await getJSON(`/rooms?code=${code}`);
  $room.innerHTML=rooms.map(r=>`<option value="${r.id}">${r.name}</option>`).join('');
}

document.getElementById('btn-create').onclick=async()=>{
  const name=$newroom.value.trim(); if(!name) return;
  const code=$country.value;
  const res=await fetch(`/rooms/create?code=${encodeURIComponent(code)}&name=${encodeURIComponent(name)}`,{method:'POST',headers:{Authorization:'Bearer '+token}});
  const data=await res.json();
  if(!res.ok){$status.textContent=data.detail||'create failed';return}
  await refreshRooms();
  $room.value=data.id; $newroom.value='';
};

document.getElementById('btn-join').onclick=()=>{
  const roomId=$room.value; if(!roomId){$status.textContent='Pick a room';return}
  location.href=`/static/chat.html?room_id=${encodeURIComponent(roomId)}`;
};

document.getElementById('btn-logout').onclick=()=>{localStorage.clear(); location.href='/static/login.html'}