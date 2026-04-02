// scan.js — Scan page logic
const uploadZone  = document.getElementById('upload-zone');
const uploadIcon  = document.getElementById('upload-icon');
const uploadText  = document.getElementById('upload-text');
const fileInput   = document.getElementById('file-input');
const cameraInput = document.getElementById('camera-input');
const btnCamera   = document.getElementById('btn-camera');
const btnGallery  = document.getElementById('btn-gallery');
const btnAnalyze  = document.getElementById('btn-analyze');
const errorMsg    = document.getElementById('error-msg');

let selectedFile = null;

function handleFile(file) {
  if (!file) return;
  if (!file.type.startsWith('image/')) { showError('Please select a valid image file.'); return; }
  if (file.size > 10 * 1024 * 1024) { showError('Image must be under 10 MB.'); return; }
  hideError();
  selectedFile = file;
  showPreview(file);
  enableAnalyze();
}

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const prev = uploadZone.querySelector('img');
    if (prev) prev.remove();
    const prevBtn = uploadZone.querySelector('.remove-btn');
    if (prevBtn) prevBtn.remove();

    const img = document.createElement('img');
    img.src = e.target.result;
    img.alt = 'Selected crop image';
    uploadZone.appendChild(img);

    const rm = document.createElement('button');
    rm.className = 'remove-btn';
    rm.innerHTML = '✕';
    rm.title = 'Remove image';
    rm.onclick = (ev) => { ev.stopPropagation(); clearSelection(); };
    uploadZone.appendChild(rm);

    uploadZone.classList.add('has-image');
    uploadIcon.style.display = 'none';
    uploadText.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

function clearSelection() {
  selectedFile = null;
  const img = uploadZone.querySelector('img');
  if (img) img.remove();
  const rm = uploadZone.querySelector('.remove-btn');
  if (rm) rm.remove();
  uploadZone.classList.remove('has-image');
  uploadIcon.style.display = '';
  uploadText.style.display = '';
  fileInput.value = '';
  cameraInput.value = '';
  disableAnalyze();
}

function enableAnalyze() {
  btnAnalyze.classList.remove('disabled');
  btnAnalyze.classList.add('ready');
}
function disableAnalyze() {
  btnAnalyze.classList.add('disabled');
  btnAnalyze.classList.remove('ready');
}
function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
}
function hideError() {
  errorMsg.style.display = 'none';
}

// Events
uploadZone.addEventListener('click', () => fileInput.click());
btnGallery.addEventListener('click', () => fileInput.click());
btnCamera.addEventListener('click', () => cameraInput.click());
fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
cameraInput.addEventListener('change', (e) => handleFile(e.target.files[0]));

// Drag & drop
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  handleFile(e.dataTransfer.files[0]);
});

// Analyze
btnAnalyze.addEventListener('click', async () => {
  if (!selectedFile) return;
  hideError();
  btnAnalyze.classList.remove('ready');
  btnAnalyze.classList.add('loading');
  btnAnalyze.innerHTML = '<div class="spinner"></div> Analyzing…';

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Analysis failed. Please try again.');
    }
    const result = await res.json();
    sessionStorage.setItem('krishiscan_result', JSON.stringify(result));
    const reader = new FileReader();
    reader.onload = (e) => {
      sessionStorage.setItem('krishiscan_image', e.target.result);
      window.location.href = '/result.html';
    };
    reader.readAsDataURL(selectedFile);
  } catch (err) {
    showError(err.message || 'Something went wrong. Please try again.');
    btnAnalyze.classList.remove('loading');
    btnAnalyze.classList.add('ready');
    btnAnalyze.innerHTML = '<svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Analyze Crop';
  }
});
