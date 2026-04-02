// result.js — Result page logic
(function () {
  const raw = sessionStorage.getItem('krishiscan_result');
  const imgSrc = sessionStorage.getItem('krishiscan_image');

  if (!raw) {
    document.getElementById('no-result').style.display = '';
    return;
  }

  document.getElementById('no-result').style.display = 'none';
  document.getElementById('result-content').style.display = '';

  const result = JSON.parse(raw);

  // Image
  if (imgSrc) {
    document.getElementById('result-image').src = imgSrc;
  }

  // Source badge
  const srcBadge = document.getElementById('result-source-badge');
  srcBadge.textContent = result.source === 'roboflow' ? '🤖 Roboflow AI' : '🧪 AI Analysis';

  // Disease name
  document.getElementById('disease-name').textContent = result.disease;

  // Icon
  const icon = document.getElementById('disease-icon');
  if (result.severity === 'None' || result.disease.toLowerCase().includes('healthy')) {
    icon.textContent = '✅';
    icon.style.background = '#dcfce7';
  } else if (result.severity === 'High') {
    icon.textContent = '🚨';
    icon.style.background = '#fef2f2';
  } else {
    icon.textContent = '⚠️';
    icon.style.background = '#fffbeb';
  }

  // Severity badge
  const sevBadge = document.getElementById('severity-badge');
  const sevClass = (result.severity || 'none').toLowerCase();
  sevBadge.textContent = result.severity === 'None' ? 'Healthy' : result.severity + ' Severity';
  sevBadge.className = 'severity-badge ' + sevClass;

  // Confidence
  document.getElementById('confidence-label').textContent = result.confidence + '% confidence';

  // Confidence bar (animate after small delay)
  setTimeout(() => {
    const bar = document.getElementById('confidence-bar');
    bar.style.width = result.confidence + '%';
    if (result.severity === 'High') bar.classList.add('high');
    else if (result.severity === 'Medium') bar.classList.add('medium');
  }, 300);

  // Treatment list
  const list = document.getElementById('treatment-list');
  (result.treatment || []).forEach((step) => {
    const li = document.createElement('li');
    li.textContent = step;
    list.appendChild(li);
  });
})();
