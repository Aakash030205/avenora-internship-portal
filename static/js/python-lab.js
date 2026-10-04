(() => {
  const lab = document.getElementById('python-lab');
  if (!lab) return;
  const editor = document.getElementById('python-code');
  const output = document.getElementById('python-output');
  const status = document.getElementById('python-status');
  const runButton = document.getElementById('python-run');
  const resetButton = document.getElementById('python-reset');
  const key = `avenora-python-${location.pathname}`;
  const starter = editor.value;
  let pyodidePromise = null;

  try { const saved = localStorage.getItem(key); if (saved !== null) editor.value = saved; } catch (_) {}
  editor.addEventListener('input', () => { try { localStorage.setItem(key, editor.value); } catch (_) {} });
  editor.addEventListener('keydown', (event) => {
    if (event.key === 'Tab') {
      event.preventDefault();
      const start = editor.selectionStart, end = editor.selectionEnd;
      editor.setRangeText('    ', start, end, 'end');
      editor.dispatchEvent(new Event('input'));
    }
  });

  async function getRuntime() {
    if (!pyodidePromise) {
      status.textContent = 'Downloading Python runtime…';
      pyodidePromise = new Promise((resolve, reject) => {
        if (window.loadPyodide) return resolve(window.loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/' }));
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js';
        script.onload = () => resolve(window.loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/' }));
        script.onerror = () => reject(new Error('Could not load Pyodide. Check your internet connection and try again.'));
        document.head.appendChild(script);
      }).then(p => p);
    }
    return await pyodidePromise;
  }

  runButton.addEventListener('click', async () => {
    runButton.disabled = true;
    output.textContent = '';
    try {
      const pyodide = await getRuntime();
      status.textContent = 'Running…';
      pyodide.setStdout({ batched: text => { output.textContent += text + '\n'; } });
      pyodide.setStderr({ batched: text => { output.textContent += text + '\n'; } });
      if (lab.dataset.lab === 'datascience' && /(^|\n)\s*(import\s+(pandas|numpy|matplotlib|sklearn)|from\s+(pandas|numpy|matplotlib|sklearn))/m.test(editor.value)) {
        status.textContent = 'Loading data-science packages…';
        const packages = [];
        if (/\b(pandas|pd)\b/.test(editor.value)) packages.push('pandas');
        if (/\b(numpy|np)\b/.test(editor.value)) packages.push('numpy');
        if (/\b(matplotlib|plt)\b/.test(editor.value)) packages.push('matplotlib');
        if (/\b(sklearn)\b/.test(editor.value)) packages.push('scikit-learn');
        if (packages.length) await pyodide.loadPackage([...new Set(packages)]);
      }
      await pyodide.runPythonAsync(editor.value);
      if (!output.textContent.trim()) output.textContent = 'Code ran successfully (no output). Use print(...) to display results.';
      status.textContent = 'Completed ✓';
    } catch (error) {
      output.textContent += (output.textContent ? '\n' : '') + String(error);
      status.textContent = 'Error — review your code';
    } finally { runButton.disabled = false; }
  });
  resetButton.addEventListener('click', () => {
    if (!confirm('Reset this lesson to its starter Python code?')) return;
    editor.value = starter;
    try { localStorage.removeItem(key); } catch (_) {}
    output.textContent = 'Starter code restored. Click “Run Python” to execute it.';
    status.textContent = 'Ready';
  });
})();
