/* ═══════════════════════════════════════════════════════
   AI Invoice Reader — Frontend Logic
   ═══════════════════════════════════════════════════════ */

let selectedFile = null;

// ─── FILE DROP ZONE ────────────────────────────────────────
const dropZone  = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault(); dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) setFile(e.target.files[0]); });

function setFile(file) {
  const allowedExts = ['.pdf','.png','.jpg','.jpeg','.tiff','.tif','.bmp','.webp'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) { showToast('Unsupported file type.', 'error'); return; }
  if (file.size > 20 * 1024 * 1024) { showToast('File too large (max 20 MB).', 'error'); return; }
  selectedFile = file;
  document.getElementById('fileIcon').textContent = ext === '.pdf' ? '📄' : '🖼️';
  document.getElementById('fileName').textContent  = file.name;
  document.getElementById('fileSize').textContent  = formatBytes(file.size);
  document.getElementById('filePreview').style.display = 'block';
  dropZone.style.display = 'none';
  document.getElementById('submitBtn').disabled = false;
}

function clearFile() {
  selectedFile = null; fileInput.value = '';
  document.getElementById('filePreview').style.display = 'none';
  dropZone.style.display = 'block';
  document.getElementById('submitBtn').disabled = true;
}

function toggleKey() {
  const inp = document.getElementById('apiKey');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

// ─── MAIN PROCESS ──────────────────────────────────────────
async function processInvoice() {
  if (!selectedFile) { showToast('Please select a file.', 'error'); return; }
  const apiKey = document.getElementById('apiKey').value.trim();
  const model  = document.getElementById('modelSelect').value;

  hideAll(); showCard('stepsCard'); setSubmitLoading(true);

  const stepsList   = document.getElementById('stepsList');
  const progressBar = document.getElementById('progressBar');
  stepsList.innerHTML = '';

  const steps = [
    { text: 'Uploading file to server…',      icon: '📤' },
    { text: 'Extracting text from document…', icon: '🔍' },
    { text: 'AI extracting all invoice fields…', icon: '🤖' },
    { text: 'Saving to Excel spreadsheet…',   icon: '💾' },
  ];

  let cur = 0;
  const ticker = setInterval(() => {
    if (cur < steps.length) {
      addStep(stepsList, steps[cur].text, steps[cur].icon, 'active');
      progressBar.style.width = `${((cur + 1) / steps.length) * 70}%`;
      cur++;
    }
  }, 800);

  try {
    const form = new FormData();
    form.append('file', selectedFile);
    if (apiKey) form.append('groq_api_key', apiKey);
    form.append('groq_model', model);

    const res  = await fetch('/api/extract', { method: 'POST', body: form });
    const data = await res.json();
    clearInterval(ticker);

    if (!res.ok) throw new Error(data.detail || 'Extraction failed.');

    stepsList.innerHTML = '';
    (data.processing_steps || []).forEach(s => addStep(stepsList, s, '✅', 'done'));
    progressBar.style.width = '100%';
    setSubmitLoading(false);

    renderResults(data);
    showCard('resultCard');
    loadRecords();
    document.getElementById('resultCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    showToast('Invoice extracted successfully!', 'success');

  } catch (err) {
    clearInterval(ticker);
    progressBar.style.width = '0%';
    addStep(stepsList, `Error: ${err.message}`, '❌', 'error');
    setSubmitLoading(false);
    showCard('errorCard');
    document.getElementById('errorMessage').innerHTML =
      `<strong>Error:</strong> ${escapeHtml(err.message)}<br/><br/>
       <small>Check your Groq API key and internet connection, then try again.</small>`;
  }
}

// ─── RENDER RESULTS ────────────────────────────────────────
function renderResults(data) {
  const inv  = data.invoice_data || {};
  const body = document.getElementById('resultBody');

  // Returns value string or null (never '—')
  const v = (k) => {
    const val = inv[k];
    if (val == null || val === '' || val === 'null' || val === 'None') return null;
    return String(val).trim();
  };

  // Build a cell only if value exists
  const cell = (label, key, highlight) => {
    const val = v(key);
    if (!val) return '';   // skip empty — don't render at all
    return `<div class="invoice-field${highlight ? ' field-highlight' : ''}">
      <div class="field-label">${label}</div>
      <div class="field-value${highlight ? ' highlight' : ''}">${escapeHtml(val)}</div>
    </div>`;
  };

  // Build a section only if at least one key has data
  const section = (title, keys, gridClass, cellsFn) => {
    const hasAny = keys.some(k => v(k));
    if (!hasAny) return '';
    return `<div class="section-title" style="margin-top:20px">${title}</div>
            <div class="invoice-grid ${gridClass}">${cellsFn()}</div>`;
  };

  let html = '';
  let extracted = 0;
  Object.keys(inv).forEach(k => { if (k !== 'line_items' && v(k)) extracted++; });

  // ── BADGES ───────────────────────────────────────────────
  if (data.saved_to_excel) {
    html += `<div class="excel-badge">
      <span style="font-size:22px">📊</span>
      <span>Saved to Excel — Row #${data.excel_row || '?'} &bull;
        <a href="/api/invoices/download" style="color:#166534;font-weight:700">⬇️ Download Excel</a>
      </span>
    </div>`;
  } else if (data.error && data.error.includes('open in another program')) {
    html += `<div class="excel-badge" style="background:#FEF9C3;border-color:#FCD34D;">
      <span style="font-size:22px">⚠️</span>
      <span style="color:#92400E"><strong>Excel file is open — close it and re-upload.</strong><br/>
      <small>${escapeHtml(data.error)}</small></span>
    </div>`;
  }
  const items = (inv.line_items || []);
  html += `<div class="success-badge">
    <span>✅</span>
    ${data.extracted_text_length.toLocaleString()} chars processed &bull;
    <strong>${extracted} fields</strong> extracted &bull;
    <strong>${items.length} line items</strong>
  </div>`;

  // ── MANDATORY ────────────────────────────────────────────
  html += `<div class="section-title">⭐ Key Invoice Fields</div>
  <div class="invoice-grid">
    ${cell('🔢 Invoice Number', 'invoice_number', false)}
    ${cell('📅 Invoice Date',   'invoice_date',   false)}
    ${cell('🏢 Vendor Name',    'vendor_name',    false)}
    ${cell('👤 Customer Name',  'customer_name',  false)}
    ${cell('💰 Total Amount',   'total_amount',   true)}
    ${cell('💱 Currency',       'currency',       false)}
  </div>`;

  // ── LINE ITEMS ────────────────────────────────────────────
  if (items.length > 0) {
    // Detect which columns have any data
    const hasCols = {
      hsn:      items.some(it => it.hsn_sac_code),
      qty:      items.some(it => it.quantity),
      unit:     items.some(it => it.unit),
      price:    items.some(it => it.unit_price),
      discount: items.some(it => it.discount),
      amount:   items.some(it => it.amount),
    };
    html += `<div class="section-title" style="margin-top:20px">📋 Item Details (${items.length} items)</div>
    <div class="table-wrapper"><table>
      <thead><tr>
        <th>#</th><th>Description</th>
        ${hasCols.hsn      ? '<th>HSN/SAC</th>'    : ''}
        ${hasCols.qty      ? '<th>Qty</th>'         : ''}
        ${hasCols.unit     ? '<th>Unit</th>'        : ''}
        ${hasCols.price    ? '<th>Unit Price</th>'  : ''}
        ${hasCols.discount ? '<th>Discount</th>'    : ''}
        ${hasCols.amount   ? '<th>Amount</th>'      : ''}
      </tr></thead><tbody>`;
    items.forEach((it, i) => {
      html += `<tr>
        <td>${i + 1}</td>
        <td>${escapeHtml(it.description || '—')}</td>
        ${hasCols.hsn      ? `<td>${escapeHtml(it.hsn_sac_code || '—')}</td>` : ''}
        ${hasCols.qty      ? `<td>${escapeHtml(it.quantity     || '—')}</td>` : ''}
        ${hasCols.unit     ? `<td>${escapeHtml(it.unit         || '—')}</td>` : ''}
        ${hasCols.price    ? `<td>${escapeHtml(it.unit_price   || '—')}</td>` : ''}
        ${hasCols.discount ? `<td>${escapeHtml(it.discount     || '—')}</td>` : ''}
        ${hasCols.amount   ? `<td><strong>${escapeHtml(it.amount || '—')}</strong></td>` : ''}
      </tr>`;
    });
    html += `</tbody></table></div>`;
  }

  // ── DATES ─────────────────────────────────────────────────
  html += section('📅 Dates',
    ['due_date','delivery_date','payment_date'], 'cols-3',
    () => cell('Due Date','due_date',false) +
          cell('Delivery Date','delivery_date',false) +
          cell('Payment Date','payment_date',false)
  );

  // ── FINANCIAL ─────────────────────────────────────────────
  html += section('💰 Financial Breakdown',
    ['subtotal','discount_overall','shipping_charges','cgst','sgst','igst','round_off'], '',
    () => cell('Subtotal',           'subtotal',         false) +
          cell('Discount (Overall)', 'discount_overall', false) +
          cell('Shipping Charges',   'shipping_charges', false) +
          cell('CGST',               'cgst',             false) +
          cell('SGST',               'sgst',             false) +
          cell('IGST',               'igst',             false) +
          cell('Round Off',          'round_off',        false)
  );

  // ── VENDOR ────────────────────────────────────────────────
  html += section('🏢 Vendor Info',
    ['vendor_name','vendor_gstin','vendor_pan','vendor_email','vendor_phone','vendor_bank_details','vendor_address'], '',
    () => cell('Vendor Name',   'vendor_name',         false) +
          cell('GSTIN',         'vendor_gstin',        false) +
          cell('PAN',           'vendor_pan',          false) +
          cell('Email',         'vendor_email',        false) +
          cell('Phone',         'vendor_phone',        false) +
          cell('Bank Details',  'vendor_bank_details', false)
  );
  if (v('vendor_address')) {
    html += `<div class="address-box"><div class="field-label">📍 Vendor Address</div>${escapeHtml(v('vendor_address'))}</div>`;
  }

  // ── CUSTOMER ──────────────────────────────────────────────
  html += section('👤 Customer Info',
    ['customer_name','customer_gstin','customer_contact','customer_address'], 'cols-3',
    () => cell('Customer Name',    'customer_name',    false) +
          cell('Customer GSTIN',   'customer_gstin',   false) +
          cell('Contact',          'customer_contact', false)
  );
  if (v('customer_address')) {
    html += `<div class="address-box"><div class="field-label">📍 Customer Address</div>${escapeHtml(v('customer_address'))}</div>`;
  }

  // ── PAYMENT ───────────────────────────────────────────────
  html += section('🏦 Payment Info',
    ['payment_method','transaction_id','payment_date','payment_status'], 'cols-4',
    () => cell('Payment Method', 'payment_method', false) +
          cell('Transaction ID', 'transaction_id', false) +
          cell('Payment Date',   'payment_date',   false) +
          cell('Payment Status', 'payment_status', false)
  );

  // ── COMPLIANCE ────────────────────────────────────────────
  html += section('📊 Compliance',
    ['place_of_supply','reverse_charge'], 'cols-3',
    () => cell('Place of Supply', 'place_of_supply', false) +
          cell('Reverse Charge',  'reverse_charge',  false)
  );

  // ── NOTES ─────────────────────────────────────────────────
  if (v('notes')) {
    html += `<div style="margin-top:20px">
      <div class="section-title">📝 Notes / Terms</div>
      <div class="address-box notes-box">${escapeHtml(v('notes'))}</div>
    </div>`;
  }

  // If almost nothing extracted
  if (extracted === 0 && items.length === 0) {
    html += `<div class="error-message">
      The AI could not extract structured data from this document.
      The text may be unclear, scanned at low quality, or not a standard invoice format.
    </div>`;
  }

  body.innerHTML = html;
}

// ─── LOAD RECORDS TABLE ────────────────────────────────────
async function loadRecords() {
  const container = document.getElementById('recordsContainer');
  container.innerHTML = `<div class="empty-state"><div class="empty-icon">⏳</div><p>Loading…</p></div>`;

  try {
    const res  = await fetch('/api/invoices');
    const data = await res.json();

    if (!data.invoices || data.invoices.length === 0) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📂</div><p>No invoices yet. Upload one above!</p></div>`;
      return;
    }

    // Show key columns only in the overview table
    const cols = [
      'S.No','File Name','Invoice Number','Invoice Date',
      'Vendor Name','Customer Name','Total Amount','Currency',
      'CGST','SGST','IGST','Payment Status','Extracted At'
    ];

    let html = `<p class="records-count">${data.total} invoice${data.total !== 1 ? 's' : ''} saved</p>
    <div class="records-table-wrapper"><table>
      <thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>`;

    data.invoices.forEach(row => {
      html += `<tr>
        <td>${row['S.No']??''}</td>
        <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(row['File Name']||'')}">${escapeHtml(row['File Name']||'—')}</td>
        <td>${escapeHtml(row['Invoice Number']||'—')}</td>
        <td>${row['Invoice Date']||'—'}</td>
        <td><strong>${escapeHtml(row['Vendor Name']||'—')}</strong></td>
        <td>${escapeHtml(row['Customer Name']||'—')}</td>
        <td><strong style="color:#4F46E5">${escapeHtml(row['Total Amount']||'—')}</strong></td>
        <td>${row['Currency']||'—'}</td>
        <td>${row['CGST']||'—'}</td>
        <td>${row['SGST']||'—'}</td>
        <td>${row['IGST']||'—'}</td>
        <td>${escapeHtml(row['Payment Status']||'—')}</td>
        <td style="color:#64748B;font-size:11px">${row['Extracted At']||'—'}</td>
      </tr>`;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;

  } catch (err) {
    container.innerHTML = `<div class="error-message">Failed to load: ${escapeHtml(err.message)}</div>`;
  }
}

// ─── HELPERS ───────────────────────────────────────────────
function addStep(list, text, icon, type) {
  const el = document.createElement('div');
  el.className = `step-item ${type}`;
  el.innerHTML = `<span class="step-status">${icon}</span><span class="step-text">${escapeHtml(text)}</span>`;
  list.appendChild(el);
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showCard(id)  { const el = document.getElementById(id); if (el) el.style.display = 'block'; }
function hideAll()     { ['stepsCard','resultCard','errorCard'].forEach(id => { const el = document.getElementById(id); if (el) el.style.display = 'none'; }); }

function setSubmitLoading(on) {
  const btn = document.getElementById('submitBtn');
  btn.disabled = on;
  btn.classList.toggle('loading', on);
  btn.innerHTML = on
    ? `<span class="spinner"></span><span class="btn-text">Processing…</span>`
    : `<span class="btn-icon">⚡</span><span class="btn-text">Extract Invoice Data</span>`;
}

function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(1) + ' MB';
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showToast(msg, type = 'success') {
  document.querySelector('.toast')?.remove();
  const t = document.createElement('div');
  t.className = 'toast';
  t.style.cssText = `position:fixed;bottom:24px;right:24px;z-index:9999;
    background:${type==='success'?'#059669':'#DC2626'};color:white;
    padding:14px 20px;border-radius:10px;font-size:14px;font-weight:600;
    font-family:var(--font);box-shadow:0 8px 24px rgba(0,0,0,.15);
    display:flex;align-items:center;gap:8px;max-width:360px;`;
  t.innerHTML = `<span>${type==='success'?'✅':'❌'}</span> ${escapeHtml(msg)}`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

document.addEventListener('DOMContentLoaded', loadRecords);
