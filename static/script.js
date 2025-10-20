const socket = io({ path: "/socket.io", transports: ["websocket", "polling"] });

const $messages = document.getElementById("messages");
const $typing = document.getElementById("typing");
const $status = document.getElementById("status");
const $input = document.getElementById("m");
const $btnSend = document.getElementById("send");
const $username = document.getElementById("username");
const $room = document.getElementById("room");
const $btnJoin = document.getElementById("btn-join");
const $file = document.getElementById("file");
const $btnUpload = document.getElementById("btn-upload");

function addLine(html) {
  const li = document.createElement("li");
  li.innerHTML = html;
  $messages.appendChild(li);
  $messages.scrollTop = $messages.scrollHeight;
}

socket.on("connect", () => {
  console.log("socket connected", socket.id);
  $status.textContent = "Connected ✔";
});

socket.on("connect_error", (err) => {
  console.error("connect_error:", err);
  $status.textContent = "Socket connect error. Check console (F12).";
});

socket.on("server_info", (data) => {
  addLine(`<em>(server)</em> ${data.message} SID=${data.sid}`);
});

socket.on("user_joined", (data) => addLine(`🔔 <b>${data.username}</b> joined <b>${data.room}</b>`));
socket.on("user_left", (data) => addLine(`🔕 <b>${data.username}</b> left <b>${data.room}</b>`));
socket.on("room_changed", (data) => addLine(`➡ moved to room: <b>${data.room}</b>`));

socket.on("typing", (data) => {
  $typing.textContent = `${data.username} is typing...`;
  clearTimeout(window._typingTimeout);
  window._typingTimeout = setTimeout(() => ($typing.textContent = ""), 600);
});

socket.on("chat_message", (msg) => {
  const time = new Date(msg.created_at).toLocaleTimeString();
  addLine(`[${time}] <b>${msg.username}</b>: ${escapeHtml(msg.text)}`);
});

socket.on("file_uploaded", (att) => {
  const time = new Date(att.created_at).toLocaleTimeString();
  const name = escapeHtml(att.original_name);
  const url = att.url;
  // preview sederhana untuk gambar
  const preview = att.mime_type && att.mime_type.startsWith("image/")
    ? `<div class="thumb"><img src="${url}" alt="${name}" /></div>`
    : `📎`;
  addLine(
    `[${time}] <b>${att.username}</b> uploaded: ${preview} <a href="${url}" download>${name}</a> <small>(${prettySize(att.size_bytes)})</small>`
  );
});

$btnSend.onclick = () => {
  const text = $input.value.trim();
  if (!text) return;
  const room = $room.value.trim();
  socket.emit("chat_message", { text, room: room || undefined });
  $input.value = "";
  $input.focus();
};

$input.addEventListener("input", () => socket.emit("typing", {}));

$btnJoin.onclick = async () => {
  const username = $username.value.trim();
  const room = $room.value.trim();

  if (username) socket.emit("set_username", { username });
  if (room) socket.emit("join_room", { room });

  // load history messages
  const qs = new URLSearchParams({ room: room || "lobby", limit: "50" }).toString();
  const res = await fetch(`/api/messages?${qs}`);
  const items = await res.json();
  $messages.innerHTML = "";
  items.forEach((m) => {
    const time = new Date(m.created_at).toLocaleTimeString();
    addLine(`[${time}] <b>${escapeHtml(m.username)}</b>: ${escapeHtml(m.text)}`);
  });

  // load last attachments
  const res2 = await fetch(`/api/attachments?${qs}`);
  const files = await res2.json();
  files.forEach((att) => {
    const time = new Date(att.created_at).toLocaleTimeString();
    const name = escapeHtml(att.original_name);
    const preview = att.mime_type && att.mime_type.startsWith("image/")
      ? `<div class="thumb"><img src="${att.url}" alt="${name}" /></div>`
      : `📎`;
    addLine(`[${time}] <b>${escapeHtml(att.username)}</b> uploaded: ${preview} <a href="${att.url}" download>${name}</a> <small>(${prettySize(att.size_bytes)})</small>`);
  });
};

$btnUpload.onclick = async () => {
  const files = $file.files;
  if (!files || !files.length) return;
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  fd.append("room", $room.value.trim() || "lobby");
  fd.append("username", $username.value.trim() || "anon");

  const res = await fetch("/api/upload", { method: "POST", body: fd });
  if (!res.ok) {
    const t = await res.text();
    alert(`Upload failed: ${t}`);
  } else {
    // server akan broadcast via socket; clear input
    $file.value = "";
  }
};

function prettySize(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n/1024).toFixed(1)} KB`;
  return `${(n/1024/1024).toFixed(1)} MB`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
