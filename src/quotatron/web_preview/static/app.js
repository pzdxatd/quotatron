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

const gridContainer = document.getElementById('grid-container');
const canvasWrap = document.querySelector('.canvas-wrap');
let gridSources = [];

function renderGrid() {
  // Close any open SSE first
  if (es) { es.close(); es = null; }
  gridSources.forEach(s => s.close());
  gridSources = [];

  fetch('/api/animations').then(r => r.json()).then(animations => {
    gridContainer.innerHTML = '';
    for (const a of animations) {
      const cell = document.createElement('div');
      cell.className = 'grid-cell';
      const c = document.createElement('canvas');
      c.width = 250; c.height = 122;
      const label = document.createElement('span');
      label.textContent = a.name;
      cell.appendChild(c); cell.appendChild(label);
      gridContainer.appendChild(cell);

      const cctx = c.getContext('2d');
      const params = new URLSearchParams({
        polarity: 'normal', rotation: 'landscape', duration: '5',
      });
      const src = new EventSource(`/api/animation/${a.name}/stream?${params}`);
      src.addEventListener('frame', e => {
        const { png_b64 } = JSON.parse(e.data);
        const img = new Image();
        img.onload = () => cctx.drawImage(img, 0, 0);
        img.src = 'data:image/png;base64,' + png_b64;
      });
      src.addEventListener('done', () => src.close());
      gridSources.push(src);
    }
  });
}

document.getElementById('grid-toggle').onclick = () => {
  const showing = !gridContainer.classList.contains('hidden');
  if (showing) {
    gridContainer.classList.add('hidden');
    canvasWrap.classList.remove('hidden');
    gridSources.forEach(s => s.close());
    gridSources = [];
  } else {
    canvasWrap.classList.add('hidden');
    gridContainer.classList.remove('hidden');
    renderGrid();
  }
};

document.getElementById('record-gif').onclick = async () => {
  if (!currentName) {
    alert('Pick an animation first');
    return;
  }
  const params = new URLSearchParams({ duration: '5' });
  const r = await fetch(`/api/animation/${currentName}/gif?${params}`, { method: 'POST' });
  if (r.ok) {
    const data = await r.json();
    alert(`Saved: ${data.path}`);
  } else {
    alert(`Failed: ${await r.text()}`);
  }
};
