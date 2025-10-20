const $email=document.getElementById('email');
const $password=document.getElementById('password');
const $name=document.getElementById('name');
const $gender=document.getElementById('gender');
const $status=document.getElementById('status');

async function call(path, body){
  const res = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await res.json();
  if(!res.ok) throw new Error(data.detail||'error');
  return data;
}

document.getElementById('btn-login').onclick=async()=>{
  try{
    const data=await call('/auth/login',{email:$email.value.trim(),password:$password.value});
    localStorage.setItem('token',data.token);
    localStorage.setItem('user_name',data.user.name);
    location.href='/static/join.html';
  }catch(e){$status.textContent='Login failed: '+e.message}
};

document.getElementById('btn-register').onclick=async()=>{
  try{
    const data=await call('/auth/register',{email:$email.value.trim(),password:$password.value,name:$name.value.trim(),gender:$gender.value});
    localStorage.setItem('token',data.token);
    localStorage.setItem('user_name',data.user.name);
    location.href='/static/join.html';
  }catch(e){$status.textContent='Register failed: '+e.message}
};