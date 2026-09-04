/* ---------- arrastar para reordenar (pointer events, funciona em touch e mouse) ---------- */
function enableDragReorder(containerEl, onReorderIds) {
  containerEl.querySelectorAll(':scope > .drag-row').forEach(row => {
    const handle = row.querySelector('.drag-handle');
    if (!handle) return;
    handle.style.touchAction = 'none';
    handle.onpointerdown = (e) => {
      e.preventDefault();
      const dragging = row;
      dragging.classList.add('dragging');
      // Capture on the container (which never moves) rather than the dragged row itself —
      // reparenting the captured element via insertBefore silently drops pointer capture in Chromium.
      containerEl.setPointerCapture(e.pointerId);

      const onMove = (ev) => {
        const rows = [...containerEl.querySelectorAll(':scope > .drag-row')].filter(r => r !== dragging);
        const y = ev.clientY;
        let inserted = false;
        for (const r of rows) {
          const rect = r.getBoundingClientRect();
          if (y < rect.top + rect.height / 2) { containerEl.insertBefore(dragging, r); inserted = true; break; }
        }
        if (!inserted && rows.length) containerEl.insertBefore(dragging, rows[rows.length - 1].nextSibling);
      };
      const onUp = () => {
        dragging.classList.remove('dragging');
        containerEl.releasePointerCapture(e.pointerId);
        containerEl.onpointermove = null;
        containerEl.onpointerup = null;
        const ids = [...containerEl.querySelectorAll(':scope > .drag-row')].map(r => r.dataset.id);
        onReorderIds(ids);
      };
      containerEl.onpointermove = onMove;
      containerEl.onpointerup = onUp;
    };
  });
}

/* ---------- arrastar (swipe) para excluir ---------- */
function enableSwipeToDelete(row, onDelete, excludeSelector) {
  let startX = 0, startY = 0, active = false, committed = false, pointerId = null;
  row.style.touchAction = 'pan-y';
  row.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (excludeSelector && e.target.closest(excludeSelector)) return;
    startX = e.clientX; startY = e.clientY; active = true; committed = false; pointerId = e.pointerId;
    row.style.transition = 'none';
    // Não captura o ponteiro ainda: um toque simples deve deixar o clique do
    // botão/input filho disparar normalmente. Só captura ao confirmar o swipe.
  });
  row.addEventListener('pointermove', (e) => {
    if (!active) return;
    const dx = e.clientX - startX, dy = e.clientY - startY;
    if (!committed) {
      if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) { committed = true; row.setPointerCapture(pointerId); }
      else if (Math.abs(dy) > 8) { active = false; return; }
    }
    if (committed) {
      const clamped = Math.min(0, Math.max(dx, -96));
      row.style.transform = `translateX(${clamped}px)`;
      row.classList.toggle('swipe-armed', clamped < -48);
    }
  });
  const finish = (e) => {
    if (!active) return;
    active = false;
    row.style.transition = 'transform .18s ease';
    const dx = e.clientX - startX;
    if (committed && dx < -48) {
      row.style.transform = 'translateX(-100%)';
      row.style.opacity = '0';
      setTimeout(onDelete, 160);
      return;
    }
    row.style.transform = 'translateX(0)';
    row.classList.remove('swipe-armed');
    if (committed) {
      const suppressClick = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
      row.addEventListener('click', suppressClick, { capture: true, once: true });
    }
    committed = false;
  };
  row.addEventListener('pointerup', finish);
  row.addEventListener('pointercancel', () => {
    active = false; committed = false;
    row.style.transition = 'transform .18s ease';
    row.style.transform = 'translateX(0)';
    row.classList.remove('swipe-armed');
  });
}

/* ---------- toast ---------- */
function toast(msg) {
  const root = document.getElementById('toastRoot');
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  root.innerHTML = '';
  root.appendChild(el);
  setTimeout(() => { if (el.parentNode) el.remove(); }, 2400);
}

/* ---------- modal genérico ---------- */
function openModal(html) {
  document.getElementById('modalRoot').innerHTML =
    `<div class="modal-backdrop" onclick="if(event.target===this) closeModal()"><div class="modal-sheet">${html}</div></div>`;
}

function closeModal() { document.getElementById('modalRoot').innerHTML = ''; }

function makeEmpty(text) {
  const div = document.createElement('div');
  div.className = 'empty';
  div.innerHTML = `<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path d="M9 12h6"/></svg><span>${esc(text)}</span>`;
  return div;
}

/* ---------- confirmação ---------- */
function confirmDialog(message, onConfirm) {
  openModal(`
    <div class="modal-title">Confirmar</div>
    <p style="font-size:14px;color:var(--muted);line-height:1.6;">${esc(message)}</p>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="cCancel">Cancelar</button>
      <button class="btn btn-danger" style="flex:1" id="cOk">Confirmar</button>
    </div>
  `);
  document.getElementById('cCancel').onclick = closeModal;
  document.getElementById('cOk').onclick = () => { closeModal(); onConfirm(); };
}
