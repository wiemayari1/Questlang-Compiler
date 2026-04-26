(function() {
 'use strict';

 var API = '';
 var currentCode = '';
 var currentFileName = '';
 var graphNet = null;
 var graphDat = null;
 var simData = null;
 var simIndex = -1;
 var simPlaying = false;
 var stepMode = false;
 var errs = [];
 var warns = [];
 var EXAMPLES = window.QUESTLANG_EXAMPLES || {};

 function init() {
 try {
 initTabs();
 initSplitter();
 initSimControls();
 initGraphFilters();
 bindEvents();
 initExamples();
 log('Forge prete.', 'info');
 } catch (e) {
 console.error('Init error:', e);
 }
 }

 function initExamples() {
 var sel = document.getElementById('example-select');
 if (!sel) return;
 var names = Object.keys(EXAMPLES);
 sel.innerHTML = '<option value="">-- Charger un exemple --</option>';
 names.forEach(function(name) {
 var o = document.createElement('option');
 o.value = name;
 o.textContent = name;
 sel.appendChild(o);
 });
 log(names.length + ' exemples charges', 'ok');
 if (names.length > 0) {
 loadCode(EXAMPLES[names[0]], names[0] + '.ql');
 }
 }

 function highlightCode(code) {
 var keywords = ['world','quest','item','npc','script','func','var','if','else','while','for','in','return','give','take','call','true','false'];
 var types = ['int','float','bool','string','list'];
 var builtins = ['start','start_gold','win_condition','title','desc','requires','unlocks','rewards','costs','condition','value','stackable','type','location','gives_quest','xp','gold'];

 var lines = code.split("\n");
 var html = '';
 lines.forEach(function(line, i) {
 var hl = line
 .replace(/\/\/.*$/g, '<span class="comment">$&</span>')
 .replace(/"(?:[^"\\]|\\.)*"/g, '<span class="string">$&</span>')
 .replace(/\b\d+\.?\d*\b/g, '<span class="number">$&</span>');

 keywords.forEach(function(kw) {
 var re = new RegExp("\b" + kw + "\b", "g");
 hl = hl.replace(re, '<span class="keyword">' + kw + '</span>');
 });
 types.forEach(function(ty) {
 var re = new RegExp("\b" + ty + "\b", "g");
 hl = hl.replace(re, '<span class="type">' + ty + '</span>');
 });
 builtins.forEach(function(bi) {
 var re = new RegExp("\b" + bi + "\b", "g");
 hl = hl.replace(re, '<span class="builtin">' + bi + '</span>');
 });

 html += '<div class="code-line"><span class="line-num">' + (i + 1) + '</span><span class="line-content">' + hl + '</span></div>';
 });
 return html;
 }

 function loadCode(code, filename) {
 currentCode = code;
 currentFileName = filename;
 var display = document.getElementById('source-display');
 if (display) display.innerHTML = highlightCode(code);
 var info = document.getElementById('file-info');
 if (info) info.textContent = filename + ' | ' + code.length + ' chars | ' + code.split("\n").length + ' lignes';
 var name = document.getElementById('file-name');
 if (name) name.textContent = filename;
 }

 function initTabs() {
 var tabs = document.querySelectorAll('.vtab');
 var panes = document.querySelectorAll('.view-pane');
 tabs.forEach(function(t) {
 t.addEventListener('click', function() {
 var target = t.dataset.tab;
 tabs.forEach(function(x) { x.classList.remove('active'); });
 panes.forEach(function(x) { x.classList.remove('active'); });
 t.classList.add('active');
 var pane = document.getElementById('view-' + target);
 if (pane) pane.classList.add('active');
 if (target === 'map' && graphNet) setTimeout(function() { graphNet.fit(); }, 100);
 });
 });
 }

 function initSplitter() {
 var dragging = false;
 var left = document.getElementById('panel-left');
 var splitter = document.getElementById('splitter');
 if (!splitter) return;
 splitter.addEventListener('mousedown', function() { dragging = true; document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none'; });
 document.addEventListener('mousemove', function(e) {
 if (!dragging) return;
 var container = document.getElementById('workspace');
 if (!container) return;
 var nw = e.clientX - container.getBoundingClientRect().left;
 if (nw >= 260 && nw <= container.offsetWidth - 280) { left.style.width = nw + 'px'; left.style.flex = 'none'; }
 });
 document.addEventListener('mouseup', function() {
 if (dragging) { dragging = false; document.body.style.cursor = ''; document.body.style.userSelect = ''; if (graphNet) graphNet.fit(); }
 });
 }

 function initSimControls() {
 var resetBtn = document.getElementById('sim-reset');
 var prevBtn = document.getElementById('sim-prev');
 var nextBtn = document.getElementById('sim-next');
 var playBtn = document.getElementById('sim-play');
 if (resetBtn) resetBtn.addEventListener('click', function() { simIndex = -1; renderSim(); });
 if (prevBtn) prevBtn.addEventListener('click', function() { if (simIndex > -1) { simIndex--; renderSim(); } });
 if (nextBtn) nextBtn.addEventListener('click', function() { if (simData && simIndex < simData.order.length - 1) { simIndex++; renderSim(); } });
 if (playBtn) playBtn.addEventListener('click', function() {
 if (simPlaying) { simPlaying = false; playBtn.textContent = '▶ Play'; return; }
 if (!simData || simData.order.length === 0) return;
 simPlaying = true; playBtn.textContent = '⏸ Pause';
 function step() {
 if (!simPlaying) return;
 if (simIndex < simData.order.length - 1) { simIndex++; renderSim(); setTimeout(step, 800); }
 else { simPlaying = false; playBtn.textContent = '▶ Play'; }
 }
 step();
 });
 }

 function initGraphFilters() {
 ['filter-quest','filter-item','filter-npc','filter-reward'].forEach(function(id) {
 var el = document.getElementById(id);
 if (el) el.addEventListener('change', applyGraphFilters);
 });
 var fitBtn = document.getElementById('btn-fit');
 if (fitBtn) fitBtn.addEventListener('click', function() { if (graphNet) graphNet.fit(); });

 // BONUS 4: Export PNG button
 var exportBtn = document.getElementById('btn-export-png');
 if (exportBtn) exportBtn.addEventListener('click', exportGraphPNG);
 }

 // BONUS 4: Export graph as PNG
 function exportGraphPNG() {
 if (!graphNet) {
 log('Aucun graphe a exporter. Compilez d\'abord.', 'warn');
 return;
 }
 try {
 // Get the canvas from vis.js network
 var canvas = document.querySelector('#map-canvas canvas');
 if (!canvas) {
 log('Canvas non trouve pour l\'export.', 'err');
 return;
 }

 // Create a temporary canvas with white background
 var tempCanvas = document.createElement('canvas');
 tempCanvas.width = canvas.width;
 tempCanvas.height = canvas.height;
 var ctx = tempCanvas.getContext('2d');

 // Fill white background
 ctx.fillStyle = '#1a1a2e';
 ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

 // Draw the original canvas on top
 ctx.drawImage(canvas, 0, 0);

 // Add title
 ctx.fillStyle = '#d8d8e8';
 ctx.font = 'bold 16px sans-serif';
 ctx.fillText('QuestLang Forge - Carte du Monde', 10, 25);
 ctx.font = '12px sans-serif';
 ctx.fillStyle = '#8a8aaa';
 ctx.fillText('Genere le ' + new Date().toLocaleString(), 10, 45);

 // Download
 var link = document.createElement('a');
 link.download = 'questlang_map_' + (currentFileName.replace('.ql', '') || 'monde') + '.png';
 link.href = tempCanvas.toDataURL('image/png');
 link.click();

 log('Graphe exporte en PNG: ' + link.download, 'ok');
 } catch (e) {
 log('Erreur d\'export PNG: ' + e.message, 'err');
 console.error('Export error:', e);
 }
 }

 function bindEvents() {
 var compileBtn = document.getElementById('btn-compile');
 var clearBtn = document.getElementById('btn-clear');
 var stepBtn = document.getElementById('btn-step');
 var clrConsole = document.getElementById('btn-clr-console');
 var exSelect = document.getElementById('example-select');
 var fileInput = document.getElementById('file-input');
 var loadBtn = document.getElementById('btn-load');

 if (compileBtn) compileBtn.addEventListener('click', compile);
 if (clearBtn) clearBtn.addEventListener('click', function() { loadCode('', 'Aucun'); clearConsole(); resetAll(); });
 if (stepBtn) stepBtn.addEventListener('click', function() {
 stepMode = !stepMode;
 stepBtn.classList.toggle('active', stepMode);
 stepBtn.textContent = stepMode ? 'Continu' : 'Pas-a-pas';
 log(stepMode ? 'Mode pas-a-pas' : 'Mode continu', 'info');
 });
 if (clrConsole) clrConsole.addEventListener('click', function() { var body = document.getElementById('console-body'); if (body) body.innerHTML = ''; });
 if (exSelect) exSelect.addEventListener('change', function(e) {
 var name = e.target.value;
 if (name && EXAMPLES[name]) {
 loadCode(EXAMPLES[name], name + '.ql');
 log('Charge: ' + name, 'info');
 }
 });

 if (fileInput) {
 fileInput.addEventListener('change', function(e) {
 var file = e.target.files[0];
 if (!file) return;
 var reader = new FileReader();
 reader.onload = function(evt) {
 loadCode(evt.target.result, file.name);
 log('Fichier charge: ' + file.name, 'ok');
 };
 reader.onerror = function() {
 log('Erreur de lecture du fichier', 'err');
 };
 reader.readAsText(file);
 });
 }
 if (loadBtn) {
 loadBtn.addEventListener('click', function() {
 if (fileInput) fileInput.click();
 });
 }
 }

 async function compile() {
 if (!currentCode.trim()) { log('Aucun code', 'warn'); return; }
 setCompiling(true);
 clearConsole();
 resetAll();
 log('Compilation...', 'info');

 try {
 var r = await fetch(API + '/api/compile', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({ code: currentCode, step_mode: stepMode })
 });
 var d = await r.json();
 if (stepMode && d.semantic_report && d.semantic_report.passes) {
 await runStepByStep(d);
 } else {
 handleResult(d);
 }
 } catch (e) {
 log('Erreur: ' + e.message, 'err');
 } finally {
 setCompiling(false);
 }
 }

 async function runStepByStep(d) {
 handleResult(d, true);
 var passes = d.semantic_report.passes;
 for (var i = 0; i < passes.length; i++) {
 log('Passe ' + (i + 1) + '...', 'info');
 highlightPass(i + 1, passes[i]);
 await sleep(600);
 }
 log('Termine', 'ok');
 }

 function sleep(ms) { return new Promise(function(r) { setTimeout(r, ms); }); }

 function highlightPass(num, passData) {
 var card = document.getElementById('pass-' + num);
 if (!card) return;
 var b = card.querySelector('.pass-badge');
 if (b) { b.className = 'pass-badge run'; b.textContent = '...'; }
 card.style.borderColor = '#c9a84c';
 setTimeout(function() {
 card.style.borderColor = '';
 if (passData.status === 'ok') { b.className = 'pass-badge ok'; b.textContent = 'OK'; }
 else if (passData.status === 'error') { b.className = 'pass-badge err'; b.textContent = 'ERR'; }
 else if (passData.status === 'warning') { b.className = 'pass-badge warn'; b.textContent = 'WARN'; }
 else { b.className = 'pass-badge pending'; b.textContent = '--'; }
 }, 400);
 }

 function handleResult(d, skipAnalysis) {
 errs = d.errors || [];
 warns = d.warnings || [];

 var statusDot = document.getElementById('status-dot');
 if (d.success) { log('OK', 'ok'); if (statusDot) statusDot.className = 'dot ok'; }
 else { log('Echec: ' + errs.length + ' err', 'err'); if (statusDot) statusDot.className = 'dot err'; }

 errs.forEach(function(e) { log('[' + (e.pass || 'ERR') + '] L' + e.line + ' ' + e.message, 'err'); });
 warns.forEach(function(w) { log('[' + (w.pass || 'WARN') + '] L' + w.line + ' ' + w.message, 'warn'); });

 if (d.compilation_details) renderCompDetails(d.compilation_details);
 if (d.semantic_report) {
 if (!skipAnalysis) renderSemanticPasses(d.semantic_report);
 if (d.semantic_report.quest_graph) renderMap(d.semantic_report.quest_graph);
 }
 if (d.simulation) { simData = d.simulation; simIndex = -1; renderSim(); }
 renderTokens(d.tokens || []);
 var astPre = document.getElementById('ast-pre');
 var irPre = document.getElementById('ir-pre');
 if (astPre) astPre.textContent = d.ast ? JSON.stringify(d.ast, null, 2) : '--';
 if (irPre) irPre.textContent = d.ir ? JSON.stringify(d.ir, null, 2) : '--';
 updateMetrics(d);
 }

 function renderCompDetails(details) {
 if (!details || !details.pipeline) return;
 details.pipeline.forEach(function(step, i) {
 var el = document.getElementById('comp-step-' + (i + 1));
 if (!el) return;
 var status = el.querySelector('.comp-status');
 var time = el.querySelector('.comp-time');
 el.className = 'comp-step ' + (step.status === 'ok' ? 'ok' : step.status === 'err' ? 'err' : 'run');
 if (status) { status.className = 'comp-status ' + step.status; status.textContent = step.status === 'ok' ? 'OK' : step.status === 'err' ? 'ERR' : '...'; }
 if (time) time.textContent = step.time || '';
 });

 var content = document.getElementById('comp-detail-content');
 if (content) {
 var html = '';
 html += '<p>Total: ' + (details.total_time || '-') + '</p>';
 html += '<p>Tokens: ' + (details.tokens_count || '-') + '</p>';
 html += '<p>AST: ' + (details.ast_nodes || '-') + ' noeuds</p>';
 content.innerHTML = html;
 }
 }

 function renderSemanticPasses(report) {
 if (!report || !report.passes) return;
 report.passes.forEach(function(p, i) {
 var card = document.getElementById('pass-' + (i + 1));
 if (!card) return;
 var badge = card.querySelector('.pass-badge');
 var metrics = document.getElementById('pass-metrics-' + (i + 1));
 var errors = document.getElementById('pass-errors-' + (i + 1));

 if (badge) {
 if (p.status === 'ok') { badge.className = 'pass-badge ok'; badge.textContent = 'OK'; }
 else if (p.status === 'error') { badge.className = 'pass-badge err'; badge.textContent = 'ERR'; }
 else if (p.status === 'warning') { badge.className = 'pass-badge warn'; badge.textContent = 'WARN'; }
 else { badge.className = 'pass-badge pending'; badge.textContent = '--'; }
 }

 if (metrics) {
 metrics.innerHTML = '';
 if (p.metrics) {
 var txt = Object.entries(p.metrics).map(function(kv) { return kv[0] + ': ' + kv[1]; }).join(' | ');
 metrics.textContent = txt;
 }
 }

 if (errors) {
 errors.innerHTML = '';
 if (p.errors) {
 p.errors.forEach(function(err) {
 var div = document.createElement('div');
 div.className = err.severity === 'error' ? 'e-item' : 'w-item';
 div.textContent = (err.line ? 'L' + err.line + ': ' : '') + err.message;
 errors.appendChild(div);
 });
 }
 }
 });
 }

 function renderMap(graph) {
 if (!graph || !graph.nodes) return;
 try {
 var nodesArr = graph.nodes.map(function(n) {
 var colors = { quest: '#9b59b6', item: '#e67e22', npc: '#1abc9c' };
 var base = colors[n.type] || '#4a9eff';
 return { id: n.id, label: n.label, color: { background: base, border: base }, shape: n.type === 'quest' ? 'box' : n.type === 'item' ? 'diamond' : 'dot', font: { color: '#d8d8e8', size: 13 }, borderWidth: 2 };
 });
 var edgesArr = (graph.edges || []).map(function(e) {
 return { from: e.from, to: e.to, label: e.type, color: { color: e.color || '#4a9eff' }, arrows: 'to', font: { color: '#8a8aaa', size: 10 }, dashes: e.dashes || false };
 });

 if (graphNet) { graphNet.destroy(); graphNet = null; }
 var container = document.getElementById('map-canvas');
 if (!container) return;

 var nodes = new vis.DataSet(nodesArr);
 var edges = new vis.DataSet(edgesArr);
 graphDat = { nodes: nodes, edges: edges };

 graphNet = new vis.Network(container, graphDat, {
 layout: { hierarchical: { direction: 'LR', sortMethod: 'directed', levelSeparation: 190, nodeSpacing: 130 } },
 physics: { enabled: false },
 interaction: { hover: true, tooltipDelay: 200, zoomView: true }
 });
 } catch (e) {
 console.error('Graph error:', e);
 }
 }

 function applyGraphFilters() {
 if (!graphNet || !graphDat) return;
 var showQuest = document.getElementById('filter-quest').checked;
 var showItem = document.getElementById('filter-item').checked;
 var showNpc = document.getElementById('filter-npc').checked;
 var showReward = document.getElementById('filter-reward').checked;
 var types = {};
 if (showQuest) types.quest = true;
 if (showItem) types.item = true;
 if (showNpc) types.npc = true;

 var nodes = graphDat.nodes.get();
 var edges = graphDat.edges.get();
 var visible = new Set();
 nodes.forEach(function(n) { if (types[n.type]) visible.add(n.id); });

 graphDat.nodes.update(nodes.map(function(n) { return { id: n.id, hidden: !types[n.type] }; }));
 graphDat.edges.update(edges.map(function(e) {
 var isReward = e.label === 'reward' || e.label === 'cost';
 return { id: e.id || (e.from + '-' + e.to), hidden: !(visible.has(e.from) && visible.has(e.to) && (!isReward || showReward)) };
 }));
 }

 function renderSim() {
 var timeline = document.getElementById('sim-timeline');
 var detailTitle = document.getElementById('sim-detail-title');
 var detailBody = document.getElementById('sim-detail-body');
 var progressBar = document.getElementById('sim-progress-bar');

 if (!simData) {
 if (timeline) timeline.innerHTML = '<p>Compilez pour simuler</p>';
 var g = document.getElementById('sim-gold'); if (g) g.textContent = '0';
 var x = document.getElementById('sim-xp'); if (x) x.textContent = '0';
 var ic = document.getElementById('sim-item-count'); if (ic) ic.textContent = '0';
 if (detailTitle) detailTitle.textContent = 'Selectionnez une etape';
 if (detailBody) detailBody.innerHTML = '';
 if (progressBar) progressBar.style.width = '0%';
 return;
 }

 var order = simData.order || [];
 var history = simData.history || [];
 var inv = simIndex >= 0 && history[simIndex] ? history[simIndex].inventory_after : simData.inventory;

 var goldEl = document.getElementById('sim-gold');
 var xpEl = document.getElementById('sim-xp');
 var itemEl = document.getElementById('sim-item-count');
 if (goldEl) goldEl.textContent = (inv && inv.gold) || 0;
 if (xpEl) xpEl.textContent = (inv && inv.xp) || 0;
 if (itemEl) itemEl.textContent = Object.keys((inv && inv.items) || {}).length;
 if (progressBar) progressBar.style.width = order.length > 0 ? ((simIndex + 1) / order.length * 100) + '%' : '0%';

 if (timeline) {
 timeline.innerHTML = '';
 order.forEach(function(qid, i) {
 var step = document.createElement('div');
 step.className = 'sim-step' + (i <= simIndex ? ' completed' : '') + (i === simIndex ? ' active' : '');
 step.innerHTML = '<div class="step-num">' + (i + 1) + '</div><div class="step-name">' + esc(qid) + '</div>';
 step.addEventListener('click', function() { simIndex = i; renderSim(); });
 timeline.appendChild(step);
 });
 }

 if (simIndex >= 0 && history[simIndex]) {
 var h = history[simIndex];
 if (detailTitle) detailTitle.textContent = h.title || h.quest;
 var body = '<p>Or: ' + ((h.inventory_after && h.inventory_after.gold) || 0) + ' | XP: ' + ((h.inventory_after && h.inventory_after.xp) || 0) + '</p>';
 var items = (h.inventory_after && h.inventory_after.items) || {};
 if (Object.keys(items).length > 0) {
 body += '<div class="item-tags">';
Object.entries(items).forEach(function(kv) { body += '<span class="item-tag">' + esc(kv[0]) + ' x' + kv[1] + '</span>'; });
body += '</div>';
 }
 if (detailBody) detailBody.innerHTML = body;
 } else {
 if (detailTitle) detailTitle.textContent = 'Depart';
 if (detailBody) detailBody.innerHTML = '<p>Or: ' + ((simData.inventory && simData.inventory.gold) || 0) + '</p>';
 }
 }

 function renderTokens(tokens) {
 var tbody = document.getElementById('tok-body');
 if (!tbody) return;
 tbody.innerHTML = '';
 if (!tokens.length) {
 tbody.innerHTML = '<tr><td colspan="4">--</td></tr>';
 return;
 }
 tokens.forEach(function(t) {
 var tr = document.createElement('tr');
 tr.innerHTML = '<td>' + t.line + '</td><td>' + t.col + '</td><td>' + esc(t.type) + '</td><td>' + esc(String(t.value)) + '</td>';
 tbody.appendChild(tr);
 });
 }

 function updateMetrics(d) {
 var ir = d.ir || {};
 var q = document.getElementById('m-quests'); if (q) q.textContent = Object.keys(ir.quests || {}).length;
 var i = document.getElementById('m-items'); if (i) i.textContent = Object.keys(ir.items || {}).length;
 var n = document.getElementById('m-npcs'); if (n) n.textContent = Object.keys(ir.npcs || {}).length;
 var e = document.getElementById('m-errs'); if (e) e.textContent = errs.length;
 var w = document.getElementById('m-warns'); if (w) w.textContent = warns.length;
 var t = document.getElementById('m-tokens'); if (t) t.textContent = (d.tokens || []).length;
 var tm = document.getElementById('m-time'); if (tm) tm.textContent = d.compilation_details ? d.compilation_details.total_time : '-';
 }

 function resetAll() {
 for (var i = 1; i <= 4; i++) {
 var step = document.getElementById('comp-step-' + i);
 if (step) { step.className = 'comp-step'; var s = step.querySelector('.comp-status'); if (s) { s.className = 'comp-status pending'; s.textContent = '--'; } var t = step.querySelector('.comp-time'); if (t) t.textContent = ''; }
 var card = document.getElementById('pass-' + i);
 if (card) { var b = card.querySelector('.pass-badge'); if (b) { b.className = 'pass-badge pending'; b.textContent = '--'; } var m = document.getElementById('pass-metrics-' + i); if (m) m.innerHTML = ''; var e = document.getElementById('pass-errors-' + i); if (e) e.innerHTML = ''; }
 }
 var content = document.getElementById('comp-detail-content');
 if (content) content.innerHTML = '<p>Chargez et compilez.</p>';
 simData = null; simIndex = -1; renderSim();
 ['m-quests','m-items','m-npcs','m-errs','m-warns','m-tokens','m-time'].forEach(function(id) {
 var el = document.getElementById(id); if (el) el.textContent = '-';
 });
 }

 function log(msg, type) {
 var body = document.getElementById('console-body');
 if (!body) return;
 var line = document.createElement('div');
 line.className = 'c-line ' + (type || 'info');
 var now = new Date();
 var t = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0') + ':' + now.getSeconds().toString().padStart(2, '0');
 line.innerHTML = '[' + t + '] ' + esc(msg);
 body.appendChild(line);
 body.scrollTop = body.scrollHeight;
 }

 function clearConsole() {
 var body = document.getElementById('console-body');
 if (body) body.innerHTML = '';
 }

 function setCompiling(on) {
 var btn = document.getElementById('btn-compile');
 if (!btn) return;
 if (on) { btn.innerHTML = '<span class="spinner"></span> Compil...'; btn.disabled = true; }
 else { btn.innerHTML = 'Compiler'; btn.disabled = false; }
 }

 function esc(t) {
 var d = document.createElement('div');
 d.textContent = t;
 return d.innerHTML;
 }

 document.addEventListener('DOMContentLoaded', init);
})();