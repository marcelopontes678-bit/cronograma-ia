// Pauta — interface (JS puro, sem build). Fala só com a API em /api.
"use strict";

const PLATAFORMAS = { instagram: "Instagram", tiktok: "TikTok", youtube: "YouTube", linkedin: "LinkedIn", x: "X", threads: "Threads" };
const FORMATOS = { reels: "Reels", carrossel: "Carrossel", post: "Post", story: "Story", short: "Short", video_longo: "Vídeo longo", thread: "Thread", artigo: "Artigo" };
const STATUS = { ideia: "Ideia", rascunho: "Rascunho", aprovado: "Aprovado", publicado: "Publicado" };
const DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

const $ = (s) => document.querySelector(s);
const estado = { token: localStorage.getItem("pauta_token"), marcas: [], marca: null, planos: [], plano: null, post: null, filtro: { plataforma: "", status: "" }, timer: null };

// ---------- utilidades ----------
function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function aviso(msg) {
  const el = $("#aviso");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(aviso.t);
  aviso.t = setTimeout(() => (el.hidden = true), 3000);
}
function dataLocal(iso) { const [a, m, d] = iso.split("-").map(Number); return new Date(a, m - 1, d); }
function isoLocal(dt) { return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`; }
function fmtData(iso) { return dataLocal(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" }); }

async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, {
    ...opcoes,
    headers: { "Content-Type": "application/json", ...(estado.token ? { Authorization: `Bearer ${estado.token}` } : {}), ...opcoes.headers },
  });
  if (r.status === 401 && estado.token) { sair(); throw new Error("Sessão expirada. Entre de novo."); }
  if (r.status === 204) return null;
  if (!r.ok) {
    let msg = `Erro ${r.status}`;
    try {
      const corpo = await r.json();
      msg = Array.isArray(corpo.detail) ? corpo.detail.map((d) => d.msg).join("; ") : corpo.detail || msg;
    } catch (_) { /* resposta sem JSON */ }
    throw new Error(msg);
  }
  return (r.headers.get("content-type") || "").includes("json") ? r.json() : r.blob();
}

function checks(container, nome, marcados) {
  container.innerHTML = Object.entries(PLATAFORMAS)
    .map(([v, n]) => `<label class="check"><input type="checkbox" name="${nome}" value="${v}" ${marcados.includes(v) ? "checked" : ""}>${n}</label>`)
    .join("");
}
function marcadosEm(form, nome) { return [...form.querySelectorAll(`input[name="${nome}"]:checked`)].map((i) => i.value); }
function opcoes(sel, mapa) { sel.innerHTML = Object.entries(mapa).map(([v, n]) => `<option value="${v}">${n}</option>`).join(""); }

document.querySelectorAll("dialog [data-fechar]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));

// ---------- autenticação ----------
let modoAuth = "login";
document.querySelectorAll(".aba").forEach((aba) =>
  aba.addEventListener("click", () => {
    modoAuth = aba.dataset.modo;
    document.querySelectorAll(".aba").forEach((a) => a.classList.toggle("ativa", a === aba));
    $(".so-cadastro").hidden = modoAuth !== "cadastro";
    $(".so-cadastro input").required = modoAuth === "cadastro";
    $("#btn-auth").textContent = modoAuth === "login" ? "Entrar" : "Criar conta";
    $("#erro-auth").textContent = "";
  })
);

$("#form-auth").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const corpo = { email: f.get("email"), senha: f.get("senha") };
  if (modoAuth === "cadastro") corpo.nome = f.get("nome");
  $("#btn-auth").disabled = true;
  try {
    const { token } = await api(`/api/auth/${modoAuth}`, { method: "POST", body: JSON.stringify(corpo) });
    estado.token = token;
    localStorage.setItem("pauta_token", token);
    await iniciar();
  } catch (err) {
    $("#erro-auth").textContent = err.message;
  } finally {
    $("#btn-auth").disabled = false;
  }
});

function sair() {
  estado.token = null;
  localStorage.removeItem("pauta_token");
  clearTimeout(estado.timer);
  $("#tela-app").hidden = true;
  $("#tela-auth").hidden = false;
}
$("#btn-sair").addEventListener("click", sair);

async function atualizarUso() {
  const eu = await api("/api/auth/eu");
  $("#nome-usuario").textContent = eu.nome;
  $("#uso").textContent = eu.plano === "gratis" ? `${eu.planos_usados_mes}/${eu.limite_planos_mes} planos este mês` : "Plano Pro";
}

async function iniciar() {
  if (!estado.token) { $("#tela-auth").hidden = false; return; }
  try {
    await atualizarUso();
  } catch (_) { sair(); return; }
  $("#tela-auth").hidden = true;
  $("#tela-app").hidden = false;
  estado.marcas = await api("/api/marcas");
  const salva = localStorage.getItem("pauta_marca");
  const marca = estado.marcas.find((m) => m.id === salva) || estado.marcas[0];
  renderMarcas();
  if (marca) await abrirMarca(marca.id); else mostrarVazio();
}

// ---------- marcas ----------
function renderMarcas() {
  $("#lista-marcas").innerHTML = estado.marcas
    .map((m) => `<button type="button" class="item-marca ${estado.marca?.id === m.id ? "ativa" : ""}" data-id="${m.id}">
        <span class="avatar">${esc(m.nome.slice(0, 1).toUpperCase())}</span><span>${esc(m.nome)}</span></button>`)
    .join("");
  document.querySelectorAll(".item-marca").forEach((b) => b.addEventListener("click", () => abrirMarca(b.dataset.id)));
}

function mostrarVazio() {
  estado.marca = null;
  $("#sem-marca").hidden = false;
  $("#painel-marca").hidden = true;
}

async function abrirMarca(id) {
  clearTimeout(estado.timer);
  estado.marca = estado.marcas.find((m) => m.id === id);
  localStorage.setItem("pauta_marca", id);
  $("#sem-marca").hidden = true;
  $("#painel-marca").hidden = false;
  $("#marca-nome").textContent = estado.marca.nome;
  $("#marca-nicho").textContent = estado.marca.nicho;
  $("#marca-plataformas").innerHTML = estado.marca.plataformas.map((p) => `<span class="chip p-${p}">${PLATAFORMAS[p]}</span>`).join("");
  renderMarcas();
  estado.planos = await api(`/api/marcas/${id}/planos`);
  const pronto = estado.planos.find((p) => p.status !== "erro") || estado.planos[0];
  renderPlanos();
  if (pronto) await abrirPlano(pronto.id); else renderSemPlano();
}

function abrirModalMarca(marca) {
  const f = $("#form-marca");
  f.reset();
  $("#titulo-modal-marca").textContent = marca ? "Editar marca" : "Nova marca";
  $("#btn-apagar-marca").hidden = !marca;
  $("#erro-marca").textContent = "";
  if (marca) {
    for (const campo of ["nome", "nicho", "publico_alvo", "tom_de_voz", "objetivo"]) f.elements[campo].value = marca[campo];
    f.elements.pilares.value = marca.pilares.join("\n");
  }
  checks($("#checks-plataformas-marca"), "plataformas", marca ? marca.plataformas : ["instagram"]);
  f.dataset.id = marca ? marca.id : "";
  $("#modal-marca").showModal();
}
$("#btn-nova-marca").addEventListener("click", () => abrirModalMarca(null));
$("#btn-primeira-marca").addEventListener("click", () => abrirModalMarca(null));
$("#btn-editar-marca").addEventListener("click", () => abrirModalMarca(estado.marca));

$("#form-marca").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  const corpo = {
    nome: f.elements.nome.value, nicho: f.elements.nicho.value, publico_alvo: f.elements.publico_alvo.value,
    tom_de_voz: f.elements.tom_de_voz.value, objetivo: f.elements.objetivo.value,
    plataformas: marcadosEm(f, "plataformas"),
    pilares: f.elements.pilares.value.split("\n").map((s) => s.trim()).filter(Boolean),
  };
  if (!corpo.plataformas.length) { $("#erro-marca").textContent = "Escolha ao menos uma plataforma."; return; }
  try {
    const id = f.dataset.id;
    const marca = await api(id ? `/api/marcas/${id}` : "/api/marcas", { method: id ? "PATCH" : "POST", body: JSON.stringify(corpo) });
    estado.marcas = id ? estado.marcas.map((m) => (m.id === id ? marca : m)) : [...estado.marcas, marca];
    $("#modal-marca").close();
    await abrirMarca(marca.id);
  } catch (err) { $("#erro-marca").textContent = err.message; }
});

$("#btn-apagar-marca").addEventListener("click", async () => {
  const id = $("#form-marca").dataset.id;
  if (!confirm("Apagar esta marca e todos os planos e posts dela?")) return;
  await api(`/api/marcas/${id}`, { method: "DELETE" });
  estado.marcas = estado.marcas.filter((m) => m.id !== id);
  $("#modal-marca").close();
  renderMarcas();
  if (estado.marcas[0]) await abrirMarca(estado.marcas[0].id); else mostrarVazio();
});

// ---------- planos ----------
function rotuloPlano(p) {
  const st = { pendente: "na fila", gerando: "gerando…", pronto: "", erro: "erro" }[p.status];
  return `${fmtData(p.data_inicio)} · ${p.semanas} sem${st ? ` · ${st}` : ""}`;
}
function renderPlanos() {
  $("#lista-planos").innerHTML = estado.planos
    .map((p) => `<button type="button" class="plano-chip s-${p.status} ${estado.plano?.id === p.id ? "ativo" : ""}" data-id="${p.id}">${esc(rotuloPlano(p))}</button>`)
    .join("");
  document.querySelectorAll(".plano-chip").forEach((b) => b.addEventListener("click", () => abrirPlano(b.dataset.id)));
}

function renderSemPlano() {
  estado.plano = null;
  $("#area-plano").innerHTML = `<div class="vazio pequeno"><h3>Nenhum plano ainda</h3>
    <p>Gere seu primeiro calendário: a IA monta as datas, os ganchos, os roteiros e as legendas.</p></div>`;
}

async function abrirPlano(id) {
  clearTimeout(estado.timer);
  estado.plano = await api(`/api/planos/${id}`);
  estado.planos = estado.planos.map((p) => (p.id === id ? { ...p, status: estado.plano.status, erro: estado.plano.erro } : p));
  renderPlanos();
  renderPlano();
  if (["pendente", "gerando"].includes(estado.plano.status)) {
    estado.timer = setTimeout(() => estado.plano?.id === id && abrirPlano(id).then(() => estado.plano.status === "pronto" && atualizarUso()), 3000);
  }
}

function renderPlano() {
  const p = estado.plano;
  const area = $("#area-plano");
  if (["pendente", "gerando"].includes(p.status)) {
    area.innerHTML = `<div class="gerando"><div class="spinner"></div><div><strong>A IA está montando seu calendário…</strong>
      <p class="muted">Leva de 30 segundos a 2 minutos. Pode deixar esta aba aberta.</p></div></div>`;
    return;
  }
  if (p.status === "erro") {
    area.innerHTML = `<div class="caixa-erro"><strong>Não deu para gerar este plano.</strong><p>${esc(p.erro)}</p>
      <button class="btn fantasma" type="button" id="btn-apagar-plano">Apagar</button></div>`;
    $("#btn-apagar-plano").addEventListener("click", apagarPlano);
    return;
  }
  const plataformas = [...new Set(p.posts.map((x) => x.plataforma))];
  area.innerHTML = `
    <div class="estrategia"><span class="rotulo">Estratégia</span><p>${esc(p.estrategia)}</p></div>
    <div class="barra">
      <select id="filtro-plataforma"><option value="">Todas as plataformas</option>
        ${plataformas.map((x) => `<option value="${x}" ${estado.filtro.plataforma === x ? "selected" : ""}>${PLATAFORMAS[x]}</option>`).join("")}</select>
      <select id="filtro-status"><option value="">Todos os status</option>
        ${Object.entries(STATUS).map(([v, n]) => `<option value="${v}" ${estado.filtro.status === v ? "selected" : ""}>${n}</option>`).join("")}</select>
      <span class="muted contagem">${progresso(p.posts)}</span>
      <span class="espaco"></span>
      <button class="btn fantasma" type="button" id="btn-csv">Exportar CSV</button>
      <button class="btn fantasma perigo" type="button" id="btn-apagar-plano">Apagar plano</button>
    </div>
    <div class="calendario">${calendario(p)}</div>`;
  $("#filtro-plataforma").addEventListener("change", (e) => { estado.filtro.plataforma = e.target.value; renderPlano(); });
  $("#filtro-status").addEventListener("change", (e) => { estado.filtro.status = e.target.value; renderPlano(); });
  $("#btn-csv").addEventListener("click", baixarCsv);
  $("#btn-apagar-plano").addEventListener("click", apagarPlano);
  document.querySelectorAll(".card-post").forEach((c) => c.addEventListener("click", () => abrirPost(c.dataset.id)));
}

function progresso(posts) {
  const feitos = posts.filter((x) => x.status === "publicado").length;
  return `${posts.length} posts · ${feitos} publicados`;
}

function calendario(p) {
  const visiveis = p.posts.filter((x) => (!estado.filtro.plataforma || x.plataforma === estado.filtro.plataforma) && (!estado.filtro.status || x.status === estado.filtro.status));
  const porDia = {};
  for (const x of visiveis) (porDia[x.data] ||= []).push(x);
  // Começa na segunda-feira da semana do início e cobre todo o período (e posts movidos para depois).
  const inicio = dataLocal(p.data_inicio);
  inicio.setDate(inicio.getDate() - ((inicio.getDay() + 6) % 7));
  const ultimaData = [p.data_inicio, ...p.posts.map((x) => x.data)].sort().pop();
  const fimPeriodo = dataLocal(p.data_inicio);
  fimPeriodo.setDate(fimPeriodo.getDate() + p.semanas * 7 - 1);
  const fim = dataLocal(ultimaData) > fimPeriodo ? dataLocal(ultimaData) : fimPeriodo;
  const hoje = isoLocal(new Date());
  let html = `<div class="cal-cab">${DIAS.map((d) => `<div>${d}</div>`).join("")}</div><div class="cal-grade">`;
  for (const d = new Date(inicio); d <= fim || d.getDay() !== 1; d.setDate(d.getDate() + 1)) {
    const iso = isoLocal(d);
    const posts = porDia[iso] || [];
    html += `<div class="cal-dia ${iso === hoje ? "hoje" : ""}"><div class="cal-num">${d.getDate()}<span>${d.toLocaleDateString("pt-BR", { month: "short" })}</span></div>
      ${posts.map(card).join("")}</div>`;
  }
  return html + "</div>";
}

function card(x) {
  return `<button type="button" class="card-post p-${x.plataforma} st-${x.status}" data-id="${x.id}">
    <span class="card-meta">${PLATAFORMAS[x.plataforma]} · ${FORMATOS[x.formato] || x.formato}</span>
    <span class="card-titulo">${esc(x.titulo)}</span>
    <span class="card-status">${STATUS[x.status]}</span></button>`;
}

async function apagarPlano() {
  if (!confirm("Apagar este plano e todos os posts dele?")) return;
  await api(`/api/planos/${estado.plano.id}`, { method: "DELETE" });
  estado.planos = estado.planos.filter((p) => p.id !== estado.plano.id);
  renderPlanos();
  if (estado.planos[0]) await abrirPlano(estado.planos[0].id); else renderSemPlano();
  await atualizarUso();
}

async function baixarCsv() {
  const blob = await api(`/api/planos/${estado.plano.id}/csv`);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `plano-${estado.plano.data_inicio}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

$("#btn-gerar").addEventListener("click", () => {
  const f = $("#form-plano");
  f.reset();
  $("#erro-plano").textContent = "";
  const amanha = new Date();
  amanha.setDate(amanha.getDate() + 1);
  f.elements.data_inicio.value = isoLocal(amanha);
  checks($("#checks-plataformas-plano"), "plataformas", estado.marca.plataformas);
  $("#modal-plano").showModal();
});

$("#form-plano").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  const corpo = {
    data_inicio: f.elements.data_inicio.value, semanas: Number(f.elements.semanas.value),
    posts_por_semana: Number(f.elements.posts_por_semana.value), plataformas: marcadosEm(f, "plataformas"), foco: f.elements.foco.value,
  };
  if (!corpo.plataformas.length) { $("#erro-plano").textContent = "Escolha ao menos uma plataforma."; return; }
  try {
    const plano = await api(`/api/marcas/${estado.marca.id}/planos`, { method: "POST", body: JSON.stringify(corpo) });
    $("#modal-plano").close();
    estado.planos = [plano, ...estado.planos];
    await abrirPlano(plano.id);
  } catch (err) { $("#erro-plano").textContent = err.message; }
});

// ---------- posts ----------
opcoes($("#sel-plataforma-post"), PLATAFORMAS);
opcoes($("#sel-formato-post"), FORMATOS);

function preencherPost(x) {
  const f = $("#form-post");
  for (const c of ["data", "plataforma", "formato", "titulo", "pilar", "gancho", "roteiro", "legenda", "cta", "status"]) f.elements[c].value = x[c];
  f.elements.hashtags.value = x.hashtags.map((h) => `#${h}`).join(" ");
}

function abrirPost(id) {
  estado.post = estado.plano.posts.find((x) => x.id === id);
  $("#erro-post").textContent = "";
  $("#instrucao-ia").value = "";
  preencherPost(estado.post);
  $("#modal-post").showModal();
}

function trocarPost(novo) {
  estado.plano.posts = estado.plano.posts.map((x) => (x.id === novo.id ? novo : x)).sort((a, b) => a.data.localeCompare(b.data));
  estado.post = novo;
  renderPlano();
}

$("#form-post").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  const corpo = Object.fromEntries(["data", "plataforma", "formato", "titulo", "pilar", "gancho", "roteiro", "legenda", "cta", "status"].map((c) => [c, f.elements[c].value]));
  corpo.hashtags = f.elements.hashtags.value.split(/[\s,]+/).filter(Boolean);
  try {
    trocarPost(await api(`/api/posts/${estado.post.id}`, { method: "PATCH", body: JSON.stringify(corpo) }));
    $("#modal-post").close();
    aviso("Post salvo.");
  } catch (err) { $("#erro-post").textContent = err.message; }
});

$("#btn-reescrever").addEventListener("click", async () => {
  const instrucao = $("#instrucao-ia").value.trim();
  if (!instrucao) { $("#instrucao-ia").focus(); return; }
  const btn = $("#btn-reescrever");
  btn.disabled = true;
  btn.textContent = "Reescrevendo…";
  try {
    const novo = await api(`/api/posts/${estado.post.id}/reescrever`, { method: "POST", body: JSON.stringify({ instrucao }) });
    trocarPost(novo);
    preencherPost(novo);
    $("#instrucao-ia").value = "";
    aviso("Post reescrito pela IA.");
  } catch (err) { $("#erro-post").textContent = err.message; }
  finally { btn.disabled = false; btn.textContent = "✦ Reescrever"; }
});

$("#btn-copiar").addEventListener("click", async () => {
  const f = $("#form-post");
  const texto = [f.elements.legenda.value, f.elements.cta.value, f.elements.hashtags.value].filter(Boolean).join("\n\n");
  await navigator.clipboard.writeText(texto);
  aviso("Legenda copiada.");
});

$("#btn-apagar-post").addEventListener("click", async () => {
  if (!confirm("Apagar este post?")) return;
  await api(`/api/posts/${estado.post.id}`, { method: "DELETE" });
  estado.plano.posts = estado.plano.posts.filter((x) => x.id !== estado.post.id);
  $("#modal-post").close();
  renderPlano();
});

iniciar();
