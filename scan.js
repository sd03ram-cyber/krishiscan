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

// Mock fallback data for when API is unavailable (e.g. GitHub Pages)
const MOCK_DISEASES = [
  { disease:"Tomato Late Blight", confidence:91, severity:"High", treatment:["Remove and destroy all infected leaves immediately","Apply copper-based fungicide (e.g., Bordeaux mixture) every 7–10 days","Avoid overhead watering — use drip irrigation instead","Ensure proper spacing between plants for air circulation","Rotate crops and avoid planting tomatoes in the same spot next season"], source:"mock" },
  { disease:"Leaf Rust", confidence:84, severity:"Medium", treatment:["Apply propiconazole-based fungicide as soon as symptoms appear","Improve air circulation by thinning dense foliage","Reduce humidity around the crop canopy","Remove heavily rusted leaves and dispose of them away from the field","Use rust-resistant crop varieties in future planting seasons"], source:"mock" },
  { disease:"Healthy Crop", confidence:97, severity:"None", treatment:["No action needed — your crop looks healthy!","Continue regular watering and fertilisation schedule","Monitor periodically for early signs of pest or disease"], source:"mock" },
  { disease:"Powdery Mildew", confidence:88, severity:"Medium", treatment:["Remove infected plant parts immediately","Apply neem oil or sulfur-based fungicide","Increase spacing between plants for better ventilation","Avoid wetting foliage during irrigation","Apply potassium bicarbonate as a preventive spray"], source:"mock" },
  { disease:"Bacterial Leaf Spot", confidence:79, severity:"High", treatment:["Remove and destroy infected leaves to prevent spread","Apply copper hydroxide bactericide every 5–7 days","Avoid working with plants when foliage is wet","Disinfect tools after handling infected plants","Use certified disease-free seeds in the next season"], source:"mock" }
];

// Analyze
btnAnalyze.addEventListener('click', async () => {
  if (!selectedFile) return;
  hideError();
  btnAnalyze.classList.remove('ready');
  btnAnalyze.classList.add('loading');
  btnAnalyze.innerHTML = '<div class="spinner"></div> Analyzing…';

  let result;
  try {
    const formData = new FormData();
    formData.append('file', selectedFile);
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'API error');
    }
    result = await res.json();
  } catch (err) {
    // Fallback to mock data (works on GitHub Pages without backend)
    result = MOCK_DISEASES[Math.floor(Math.random() * MOCK_DISEASES.length)];
  }

  sessionStorage.setItem('krishiscan_result', JSON.stringify(result));
  const reader = new FileReader();
  reader.onload = (e) => {
    sessionStorage.setItem('krishiscan_image', e.target.result);
    window.location.href = 'result.html';
  };
  reader.readAsDataURL(selectedFile);
});

