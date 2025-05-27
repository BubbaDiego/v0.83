window.addEventListener('DOMContentLoaded', () => {
  const importBtn = document.getElementById('importConfig');
  const exportBtn = document.getElementById('exportConfig');

  if (exportBtn) exportBtn.addEventListener('click', async evt => {
    evt.preventDefault();
    try {
      const resp = await fetch('/alerts/export_config');
      const data = await resp.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'alert_limits.json';
      a.click();
      URL.revokeObjectURL(url);
      if (typeof showToast === 'function') {
        showToast('✅ Exported alert_limits.json');
      }
    } catch (err) {
      if (typeof showToast === 'function') {
        showToast('❌ Failed to export alert limits', true);
      }
    }
  });

  if (importBtn) importBtn.addEventListener('click', evt => {
    evt.preventDefault();
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.addEventListener('change', async () => {
      const file = input.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const payload = JSON.parse(text);
        const resp = await fetch('/alerts/import_config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
          if (typeof showToast === 'function') {
            showToast('✅ Configuration imported');
          }
          location.reload();
        } else {
          const msg = data.error || resp.statusText;
          if (typeof showToast === 'function') {
            showToast(`❌ Import failed: ${msg}`, true);
          }
        }
      } catch (err) {
        if (typeof showToast === 'function') {
          showToast('❌ Error importing alert limits', true);
        }
      }
    });
    input.click();
  });
});
