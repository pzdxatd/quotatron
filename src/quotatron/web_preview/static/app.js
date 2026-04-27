const list = document.getElementById('animations');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const counter = document.getElementById('frame-counter');
let currentName = null;
let currentLi = null;
let es = null;

async function loadList() {
  const r = await fetch('/api/animations');
  const data = await r.json();
  list.innerHTML = '';
  for (const a of data) {
    const li = document.createElement('li');
    li.textContent = a.name;
    li.dataset.duration = a.duration_default;
    li.onclick = () => {
      if (currentLi) currentLi.classList.remove('active');
      currentLi = li;
      li.classList.add('active');
      currentName = a.name;
      play();
    };
    list.appendChild(li);
  }
}

function play() {
  if (es) es.close();
  if (!currentName) return;
  const params = new URLSearchParams({
    polarity: document.getElementById('polarity').value,
    rotation: document.getElementById('rotation').value,
    duration: document.getElementById('duration').value,
  });
  es = new EventSource(`/api/animation/${currentName}/stream?${params}`);
  es.addEventListener('frame', e => {
    const { i, png_b64 } = JSON.parse(e.data);
    const img = new Image();
    img.onload = () => ctx.drawImage(img, 0, 0);
    img.src = 'data:image/png;base64,' + png_b64;
    counter.textContent = `Frame: ${i + 1}`;
  });
  es.addEventListener('done', () => { es.close(); es = null; });
}

document.getElementById('play').onclick = play;
document.getElementById('pause').onclick = () => { if (es) { es.close(); es = null; } };
loadList();
