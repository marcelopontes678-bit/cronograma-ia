function renderLineChartSVG(points, unit) {
  const W = 300, H = 140, padL = 34, padR = 12, padT = 14, padB = 22;
  const values = points.map(p => p.value);
  let min = Math.min(...values), max = Math.max(...values);
  if (min === max) { min -= 5; max += 5; }
  const range = max - min;
  const stepX = (W - padL - padR) / (points.length - 1);
  const coords = points.map((p, i) => {
    const x = padL + i * stepX;
    const y = padT + (H - padT - padB) * (1 - (p.value - min) / range);
    return { x, y, v: p.value, d: p.date };
  });
  const linePath = coords.map((c, i) => (i === 0 ? 'M' : 'L') + c.x.toFixed(1) + ',' + c.y.toFixed(1)).join(' ');
  const areaPath = linePath + ` L${coords[coords.length-1].x.toFixed(1)},${(H-padB).toFixed(1)} L${coords[0].x.toFixed(1)},${(H-padB).toFixed(1)} Z`;
  const dots = coords.map(c => `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="3.2" fill="#2dd4bf" stroke="#0d0d0f" stroke-width="1.5"/>`).join('');
  const firstLabel = formatDateShort(coords[0].d), lastLabel = formatDateShort(coords[coords.length-1].d);
  return `
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;overflow:visible;">
      <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${H-padB}" stroke="#2a2a2e" stroke-width="1"/>
      <line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}" stroke="#2a2a2e" stroke-width="1"/>
      <text x="2" y="${padT+4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${Math.round(max)}${unit}</text>
      <text x="2" y="${H-padB}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${Math.round(min)}${unit}</text>
      <path d="${areaPath}" fill="#2dd4bf22" stroke="none"/>
      <path d="${linePath}" fill="none" stroke="#2dd4bf" stroke-width="2"/>
      ${dots}
      <text x="${padL}" y="${H-4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${esc(firstLabel)}</text>
      <text x="${W-padR}" y="${H-4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono" text-anchor="end">${esc(lastLabel)}</text>
    </svg>
  `;
}

/* ---------- diagrama corporal simplificado (frente/costas) ---------- */
function bodyDiagramSVG(activeMuscles) {
  const on = (m) => activeMuscles.has(m) ? 'var(--accent)' : 'var(--surface2)';
  const skin = 'var(--border)';
  return `
    <svg viewBox="0 0 220 250" style="width:100%;max-width:240px;margin:0 auto;display:block;">
      <g>
        <circle cx="55" cy="20" r="15" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="33" y="37" width="44" height="16" rx="6" fill="${on('Ombros')}" stroke="${skin}"/>
        <rect x="37" y="53" width="36" height="48" rx="10" fill="${on('Peito')}" stroke="${skin}"/>
        <rect x="37" y="101" width="36" height="30" rx="8" fill="${on('Abdômen')}" stroke="${skin}"/>
        <rect x="18" y="55" width="15" height="52" rx="7" fill="${on('Bíceps')}" stroke="${skin}"/>
        <rect x="77" y="55" width="15" height="52" rx="7" fill="${on('Bíceps')}" stroke="${skin}"/>
        <rect x="37" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <rect x="56" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <text x="55" y="238" text-anchor="middle" font-size="9" fill="var(--muted)" font-family="IBM Plex Mono" letter-spacing="1">FRENTE</text>
      </g>
      <g transform="translate(110,0)">
        <circle cx="55" cy="20" r="15" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="33" y="37" width="44" height="16" rx="6" fill="${on('Ombros')}" stroke="${skin}"/>
        <rect x="37" y="53" width="36" height="48" rx="10" fill="${on('Costas')}" stroke="${skin}"/>
        <rect x="37" y="101" width="36" height="30" rx="8" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="18" y="55" width="15" height="52" rx="7" fill="${on('Tríceps')}" stroke="${skin}"/>
        <rect x="77" y="55" width="15" height="52" rx="7" fill="${on('Tríceps')}" stroke="${skin}"/>
        <rect x="37" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <rect x="56" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <text x="55" y="238" text-anchor="middle" font-size="9" fill="var(--muted)" font-family="IBM Plex Mono" letter-spacing="1">COSTAS</text>
      </g>
    </svg>
  `;
}
