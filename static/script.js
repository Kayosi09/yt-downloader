function writeToTerminal(text, delay = 50) {
  const terminalOutput = document.getElementById('terminal-output');
  const cursor = document.querySelector('.cursor');
  cursor.style.display = 'none';

  let i = 0;
  const interval = setInterval(() => {
    if (i < text.length) {
      terminalOutput.innerHTML += text[i];
      i++;
    } else {
      clearInterval(interval);
      cursor.style.display = 'inline-block';
    }
  }, delay);
}

function simulateProgress() {
  const terminalOutput = document.getElementById('terminal-output');
  terminalOutput.innerHTML = "";
  writeToTerminal("Starting download...\n", 30);

  setTimeout(() => writeToTerminal("\nFetching video info...\n", 30), 1500);
  setTimeout(() => writeToTerminal("\nSelecting best format...\n", 30), 3000);
  setTimeout(() => writeToTerminal("\nDownloading: [#######..........] 35%\n", 30), 5000);
  setTimeout(() => writeToTerminal("\nDownloading: [###############..] 85%\n", 30), 7000);
  setTimeout(() => writeToTerminal("\nDownload complete.\n", 30), 9000);
}

function startDownload() {
  const url = document.getElementById('url').value.trim();
  const statusDiv = document.getElementById('status');
  const downloadDiv = document.getElementById('download-link');
  const downloadBtn = document.getElementById('downloadBtn');

  downloadBtn.disabled = true;
  statusDiv.innerText = "";
  downloadDiv.innerHTML = "";

  simulateProgress();

  fetch('/api/download', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ url })
  })
  .then(res => res.json())
  .then(data => {
    if (data.file) {
      writeToTerminal(`\n✅ Download ready: <a href="/api/download/${data.file}" target="_blank">Click to download</a>\n`);
    } else {
      writeToTerminal("\n❌ Download failed.\n");
    }
  })
  .catch(err => {
    if (err.message.includes('429')) {
      writeToTerminal("\n⏳ Rate limit exceeded. Please wait.\n");
    } else {
      writeToTerminal(`\n❌ Error: ${err.message}\n`);
    }
  })
  .finally(() => {
    downloadBtn.disabled = false;
  });
}
