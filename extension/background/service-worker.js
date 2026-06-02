// SAARTHI AI — Background Service Worker
// Listens for hotkey and proxies API calls (bypasses CORS)

chrome.commands.onCommand.addListener((command) => {
  if (command === 'activate-saarthi') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle-panel' });
      }
    });
  }
});

// Proxy API requests from content script to bypass CORS
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'api-request') {
    handleApiRequest(msg)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true; // Keep message channel open for async response
  }
});

async function handleApiRequest(msg) {
  const { url, method, body, bodyType } = msg;

  const options = { method: method || 'GET' };

  if (bodyType === 'formdata') {
    // Reconstruct FormData from ArrayBuffer
    const blob = new Blob([new Uint8Array(body.data)], { type: body.mimeType });
    const formData = new FormData();
    formData.append('file', blob, body.filename);
    options.body = formData;
  } else if (body) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errText}`);
  }

  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('audio') || contentType.includes('octet-stream')) {
    // Return audio as ArrayBuffer
    const buffer = await response.arrayBuffer();
    return { type: 'audio', data: Array.from(new Uint8Array(buffer)), mimeType: contentType };
  }

  return { type: 'json', data: await response.json() };
}
