/* ========================================================
   DEMON CORE - Client condiviso del gateway (porta 8888)
   War Room e Voice Cockpit: chiamate API, voce, log, escaping.
   ======================================================== */
(function () {
  // Servito dal gateway usa percorsi relativi; aperto da file:// punta al gateway locale
  const API = location.port === '8888' ? '' : 'http://127.0.0.1:8888';

  const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => HTML_ESCAPES[c]);
  }

  // Riga di terminale: [ora] colorata con la classe indicata, messaggio come testo semplice
  function logLine(box, msg, colorClass) {
    const row = document.createElement('div');
    const stamp = document.createElement('span');
    stamp.className = colorClass;
    stamp.textContent = `[${new Date().toLocaleTimeString()}]`;
    row.append(stamp, ` ${msg}`);
    box.appendChild(row);
    box.scrollTop = box.scrollHeight;
  }

  // Restituisce il risultato del gateway, o null se risponde con errore.
  // Lancia se il gateway non è raggiungibile: il chiamante decide il fallback.
  async function sendCommand(text) {
    const res = await fetch(`${API}/api/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    return res.ok ? res.json() : null;
  }

  // Telemetria CPU/RAM (psutil); stessa semantica di sendCommand
  async function fetchSystemStats() {
    const res = await fetch(`${API}/api/system_stats`);
    return res.ok ? res.json() : null;
  }

  // Voce neurale edge-tts servita dal gateway; silenziosa se offline
  async function speak(text) {
    try {
      const res = await fetch(`${API}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (res.ok) {
        const audioUrl = URL.createObjectURL(await res.blob());
        const audio = new Audio(audioUrl);
        audio.onended = () => URL.revokeObjectURL(audioUrl);
        audio.play();
      }
    } catch (e) {
      console.log("TTS offline, uso fallback silenzioso:", e);
    }
  }

  // Web Speech API (Chrome / Edge): null se il browser non la supporta
  function initSpeech({ lang = 'it-IT', onStart, onResult, onError, onEnd }) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const recognition = new SpeechRecognition();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => onStart && onStart();
    recognition.onresult = (event) => onResult(event.results[0][0].transcript);
    recognition.onerror = (event) => onError && onError(event.error);
    recognition.onend = () => onEnd && onEnd();
    return recognition;
  }

  // [Spazio] attiva il microfono, tranne quando il focus è su un controllo che usa già lo Spazio
  function bindSpaceToMic(toggle) {
    document.addEventListener('keydown', (event) => {
      if (event.code !== 'Space' || event.repeat) return;
      if (event.target.closest('button, input, textarea, select, label, [contenteditable]')) return;
      event.preventDefault();
      toggle();
    });
  }

  window.DEMON = Object.freeze({ API, escapeHtml, logLine, sendCommand, fetchSystemStats, speak, initSpeech, bindSpaceToMic });
})();
