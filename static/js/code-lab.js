(() => {
  const lab = document.getElementById('code-lab');
  if (!lab || !window.AVENORA_LESSON) return;

  const lesson = window.AVENORA_LESSON;
  const key = `avenora-code-${lesson.id}`;
  const html = document.getElementById('html-code');
  const css = document.getElementById('css-code');
  const js = document.getElementById('js-code');
  const preview = document.getElementById('code-preview');
  const status = document.getElementById('run-status');
  const consoleBox = document.getElementById('console-box');

  const defaults = { html: lesson.html, css: lesson.css, js: lesson.js };

  function loadCode() {
    try {
      const saved = JSON.parse(localStorage.getItem(key));
      html.value = saved?.html ?? defaults.html;
      css.value = saved?.css ?? defaults.css;
      js.value = saved?.js ?? defaults.js;
    } catch (_) {
      html.value = defaults.html;
      css.value = defaults.css;
      js.value = defaults.js;
    }
  }

  function saveCode() {
    localStorage.setItem(key, JSON.stringify({ html: html.value, css: css.value, js: js.value }));
  }

  function escapeForScript(value) {
    return value.replace(/<\/script/gi, '<\\/script');
  }

  function runCode() {
    saveCode();
    consoleBox.hidden = true;
    consoleBox.textContent = '';
    status.textContent = 'Running…';

    const safeJs = escapeForScript(js.value);
    const srcdoc = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>${css.value}</style>
</head>
<body>
${html.value}
<script>
window.onerror = function(message, source, line, column) {
  parent.postMessage({ type: 'avenora-error', message: String(message) + ' (line ' + line + ')' }, '*');
};
window.addEventListener('unhandledrejection', function(event) {
  parent.postMessage({ type: 'avenora-error', message: String(event.reason) }, '*');
});
try {
${safeJs}
} catch (error) {
  parent.postMessage({ type: 'avenora-error', message: error.message }, '*');
}
<\/script>
</body>
</html>`;

    preview.srcdoc = srcdoc;
    preview.onload = () => {
      status.textContent = 'Running ✓';
    };
  }

  function resetCode() {
    if (!confirm('Reset this lesson to the original starter code?')) return;
    localStorage.removeItem(key);
    loadCode();
    runCode();
  }

  document.querySelectorAll('.editor-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.editor-tab').forEach((t) => t.classList.remove('active'));
      document.querySelectorAll('.editor-panel').forEach((p) => p.classList.remove('active'));
      tab.classList.add('active');
      document.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add('active');
    });
  });

  [html, css, js].forEach((editor) => {
    editor.addEventListener('input', () => {
      status.textContent = 'Unsaved changes';
      saveCode();
    });
    editor.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') {
        event.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.slice(0, start) + '  ' + editor.value.slice(end);
        editor.selectionStart = editor.selectionEnd = start + 2;
        saveCode();
      }
    });
  });

  document.getElementById('run-code').addEventListener('click', runCode);
  document.getElementById('reset-code').addEventListener('click', resetCode);

  window.addEventListener('message', (event) => {
    if (!event.data || event.data.type !== 'avenora-error') return;
    consoleBox.hidden = false;
    consoleBox.textContent = `JavaScript error: ${event.data.message}`;
    status.textContent = 'Error — check your JavaScript';
  });

  loadCode();
  runCode();
})();
