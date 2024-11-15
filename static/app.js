const dropArea = document.getElementById('dropArea');
const imageInput = document.getElementById('imageInput');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight() {
  dropArea.classList.add('hover');
}

function unhighlight() {
  dropArea.classList.remove('hover');
}

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const file = dt.files[0];
  processFile(file);
}

// Handle file selection via click
dropArea.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', () => {
  processFile(imageInput.files[0]);
});

function processFile(file) {
  const formData = new FormData();
  formData.append('image', file);

  fetch('http://127.0.0.1:5000/analyze', {  // Ensure the correct URL is used here
      method: 'POST',
      body: formData,
  })
  .then(response => response.json())
  .then(data => {
      document.getElementById('responseArea').innerText = JSON.stringify(data, null, 2);
  })
  .catch(error => console.error('Error:', error));
}
