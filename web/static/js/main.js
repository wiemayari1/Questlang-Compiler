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
var edgeCounter = 0;
var simTimer = null;

function init() {
    try {
        initTabs();
        initSplitter();
        initSimControls();
        initGraphFilters();
        bindEvents();
        initExamples();
        checkBackendHealth();
        log('QuestLang Forge pret.', 'info');
    } catch (e) {
        console.error('Init error:', e);
        log("Erreur d'initialisation: " + e.message, 'err');
    }
}

function checkBackendHealth() {
    fetch(API + '/api/health')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.status === 'ok') {
                log('Backend connecte. Modules: ' + d.modules.join(', '), 'ok');
            } else {
                log('Backend erreur: ' + d.message, 'err');
            }
        })
        .catch(function(e) {
            log('Backend inaccessible: ' + e.message + ' - Verifiez que le serveur Flask tourne.', 'err');
        });
}

function initExamples() {
    var sel = document.getElementById('example-select');
    if (!sel) return;
    var names = Object.keys(EXAMPLES);
    if (names.length === 0) {
        log('Aucun exemple charge', 'warn');
        return;
    }
    log(names.length + ' exemples charges', 'ok');
    if (names.length > 0) {
        loadCode(EXAMPLES[names[0]], names[0] + '.ql');
        sel.value = names[0];
    }
}

function highlightCode(code) {
    var keywords = ['world','quest','item','npc','script','func','var','if','else','while','for','in','return','give','take','call','true','false'];
    var builtins = ['start','start_gold','win_condition','title','desc','requires','unlocks','rewards','costs','condition','value','stackable','type','location','gives_quest','xp','gold'];

    var lines = code.split("\n");
    var html = '';
    lines.forEach(function(line, i) {
        var text = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        var placeholders = [];
        var phIndex = 0;

        function addPH(content) {
            var key = "___PH" + (phIndex++) + "___";
            placeholders.push({key: key, value: content});
            return key;
        }

        text = text.replace(/(\/\/.*$)/g, function(m) {
            return addPH('<span class="token-comment">' + m + '</span>');
        });
        text = text.replace(/("(?:[^"\\]|\\.)*")/g, function(m) {
            return addPH('<span class="token-string">' + m + '</span>');
        });
        text = text.replace(/\b(\d+\.?\d*)\b/g, function(m) {
            return addPH('<span class="token-number">' + m + '</span>');
        });
        keywords.forEach(function(kw) {
            var re = new RegExp('\\b(' + kw + ')\\b', 'g');
            text = text.replace(re, function(m) {
                return addPH('<span class="token-keyword">' + m + '</span>');
            });
        });
        builtins.forEach(function(bi) {
            var re = new RegExp('\\b(' + bi + ')\\b', 'g');
            text = text.replace(re, function(m) {
                return addPH('<span class="token-builtin">' + m + '</span>');
            });
        });
        placeholders.forEach(function(ph) {
            text = text.split(ph.key).join(ph.value);
        });

        html += '<div class="code-line"><span class="line-num">' + (i + 1) + '</span><span class="line-content">' + (text || ' ') + '</span></div>';
    });
    return html;
}

function loadCode(code, filename) {
    currentCode = code || '';
    currentFileName = filename || 'sans-titre.ql';
    var display = document.getElementById('source-display');
    if (display) {
        if (currentCode.trim()) {
            display.innerHTML = highlightCode(currentCode);
        } else {
            display.innerHTML = '<div class="code-line"><span class="line-num">1</span><span class="line-content token-comment">// Chargez un exemple et compilez.</span></div>';
        }
    }
    var info = document.getElementById('file-info');
    if (info) info.textContent = '| ' + currentCode.length + ' chars | ' + currentCode.split("\n").length + ' lignes';
    var name = document.getElementById('file-name');
    if (name) name.textContent = currentFileName;
    var sname = document.getElementById('source-file-name');
    if (sname) sname.textContent = currentFileName;
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
            if (target === 'map' && graphNet && typeof graphNet.fit === 'function') {
                setTimeout(function() { graphNet.fit(); }, 150);
            }
        });
    });
}

function initSplitter() {
    var dragging = false;
    var left = document.getElementById('panel-left');
    var splitter = document.getElementById('splitter');
    if (!splitter || !left) return;

    splitter.addEventListener('mousedown', function(e) {
        dragging = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
        if (!dragging) return;
        var container = document.getElementById('workspace');
        if (!container) return;
        var rect = container.getBoundingClientRect();
        var nw = e.clientX - rect.left;
        var minW = 260, maxW = container.offsetWidth - 280;
        if (nw >= minW && nw <= maxW) {
            left.style.width = nw + 'px';
            left.style.flex = 'none';
        }
    });
    document.addEventListener('mouseup', function() {
        if (dragging) {
            dragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            if (graphNet && typeof graphNet.fit === 'function') {
                setTimeout(function() { graphNet.fit(); }, 50);
            }
        }
    });
}

function initSimControls() {
    var resetBtn = document.getElementById('sim-reset');
    var prevBtn = document.getElementById('sim-prev');
    var nextBtn = document.getElementById('sim-next');
    var playBtn = document.getElementById('sim-play');

    if (resetBtn) resetBtn.addEventListener('click', function() {
        simIndex = -1; simPlaying = false;
        if (playBtn) playBtn.textContent = 'Play';
        if (simTimer) { clearTimeout(simTimer); simTimer = null; }
        renderSim();
    });
    if (prevBtn) prevBtn.addEventListener('click', function() {
        if (simIndex > -1) { simIndex--; renderSim(); }
    });
    if (nextBtn) nextBtn.addEventListener('click', function() {
        if (simData && simData.order && simIndex < simData.order.length - 1) {
            simIndex++; renderSim();
        }
    });
    if (playBtn) playBtn.addEventListener('click', function() {
        if (simPlaying) {
            simPlaying = false; playBtn.textContent = 'Play';
            if (simTimer) { clearTimeout(simTimer); simTimer = null; }
            return;
        }
        if (!simData || !simData.order || simData.order.length === 0) return;
        simPlaying = true; playBtn.textContent = 'Pause';
        function step() {
            if (!simPlaying) return;
            if (simData && simData.order && simIndex < simData.order.length - 1) {
                simIndex++; renderSim();
                simTimer = setTimeout(step, 800);
            } else {
                simPlaying = false; playBtn.textContent = 'Play';
            }
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
    if (fitBtn) fitBtn.addEventListener('click', function() {
        if (graphNet && typeof graphNet.fit === 'function') graphNet.fit();
    });
    var exportBtn = document.getElementById('btn-export-png');
    if (exportBtn) exportBtn.addEventListener('click', exportGraphPNG);
}

function exportGraphPNG() {
    if (!graphNet) { log("Aucun graphe. Compilez d'abord.", 'warn'); return; }
    try {
        var canvas = document.querySelector('#map-canvas canvas');
        if (!canvas) { log("Canvas non trouve.", 'err'); return; }
        var tmp = document.createElement('canvas');
        tmp.width = canvas.width; tmp.height = canvas.height;
        var ctx = tmp.getContext('2d');
        ctx.fillStyle = '#0e0e18';
        ctx.fillRect(0, 0, tmp.width, tmp.height);
        ctx.drawImage(canvas, 0, 0);
        var link = document.createElement('a');
        link.download = 'questlang_map.png';
        link.href = tmp.toDataURL('image/png');
        link.click();
        log('Graphe exporte.', 'ok');
    } catch (e) {
        log("Erreur export PNG: " + e.message, 'err');
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
    if (clearBtn) clearBtn.addEventListener('click', function() {
        loadCode('', 'Aucun'); clearConsole(); resetAll();
    });
    if (stepBtn) stepBtn.addEventListener('click', function() {
        stepMode = !stepMode;
        stepBtn.classList.toggle('active', stepMode);
        stepBtn.textContent = stepMode ? 'Continu' : 'Pas-a-pas';
        log(stepMode ? 'Mode pas-a-pas active' : 'Mode continu', 'info');
    });
    if (clrConsole) clrConsole.addEventListener('click', function() {
        var body = document.getElementById('console-body');
        if (body) body.innerHTML = '';
    });
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
            reader.readAsText(file);
        });
    }
    if (loadBtn) loadBtn.addEventListener('click', function() {
        if (fileInput) fileInput.click();
    });

    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            compile();
        }
    });
}

async function compile() {
    if (!currentCode || !currentCode.trim()) {
        log('Aucun code source a compiler. Chargez un exemple.', 'warn');
        return;
    }
    setCompiling(true);
    clearConsole();
    resetAll();
    log('Compilation en cours... (Ctrl+Enter pour relancer)', 'info');

    var controller = new AbortController();
    var timeoutId = setTimeout(function() { controller.abort(); }, 15000);

    try {
        var r = await fetch(API + '/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: currentCode, step_mode: stepMode }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        var d;
        var contentType = r.headers.get('content-type') || '';

        if (contentType.includes('application/json')) {
            try {
                d = await r.json();
            } catch (jsonErr) {
                log("Reponse JSON invalide du serveur: " + jsonErr.message, 'err');
                setCompiling(false);
                return;
            }
        } else {
            var text = await r.text();
            log('Erreur HTTP ' + r.status + ' (reponse non-JSON): ' + text.substring(0, 300), 'err');
            setCompiling(false);
            return;
        }

        if (!r.ok) {
            var msg = (d && d.message) || (d && d.error) || 'Erreur serveur ' + r.status;
            log('Erreur serveur [' + r.status + ']: ' + msg, 'err');
            if (d && d.traceback) console.error('Backend traceback:', d.traceback);
            setCompiling(false);
            return;
        }

        if (!d) {
            log('Reponse vide du serveur', 'err');
            setCompiling(false);
            return;
        }

        handleResult(d);

        if (d.semantic_report && d.semantic_report.quest_graph &&
            d.semantic_report.quest_graph.nodes && d.semantic_report.quest_graph.nodes.length > 0) {
            setTimeout(function() {
                var mapTab = document.querySelector('.vtab[data-tab="map"]');
                if (mapTab) mapTab.click();
            }, 300);
        }

    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            log('Timeout: le serveur ne repond pas (>15s). Verifiez que Flask tourne.', 'err');
        } else {
            log('Erreur reseau: ' + e.message, 'err');
        }
        console.error('Compile error:', e);
    } finally {
        clearTimeout(timeoutId);
        setCompiling(false);
    }
}

function handleResult(d) {
    if (!d) { log('Donnees manquantes', 'err'); return; }

    errs = d.errors || [];
    warns = d.warnings || [];

    var statusDot = document.getElementById('status-dot');

    if (d.success && errs.length === 0) {
        log('✓ Compilation reussie !', 'ok');
        if (statusDot) statusDot.className = 'dot ok';
    } else {
        if (errs.length === 0 && warns.length === 0) {
            log("✗ Echec de compilation (aucun detail d'erreur retourne)", 'err');
        } else {
            log('✗ Echec: ' + errs.length + ' erreur(s), ' + warns.length + ' avertissement(s)', 'err');
        }
        if (statusDot) statusDot.className = 'dot err';
    }

    errs.forEach(function(e) {
        var loc = e.line ? ' [L' + e.line + ']' : '';
        log('[ERREUR] ' + (e.code || '') + loc + ': ' + e.message, 'err');
    });
    warns.forEach(function(w) {
        var loc = w.line ? ' [L' + w.line + ']' : '';
        log('[ALERTE] ' + (w.code || '') + loc + ': ' + w.message, 'warn');
    });

    if (d.compilation_details) renderCompDetails(d.compilation_details);
    if (d.semantic_report) {
        renderSemanticPasses(d.semantic_report);
        if (d.semantic_report.quest_graph) {
            renderMap(d.semantic_report.quest_graph);
        }
    }
    if (d.simulation) {
        simData = d.simulation;
        simIndex = -1;
        simPlaying = false;
        var playBtn = document.getElementById('sim-play');
        if (playBtn) playBtn.textContent = 'Play';
        renderSim();
        log('Simulation: ' + (d.simulation.order || []).length + " quete(s) dans l'ordre", 'info');
    }
    renderTokens(d.tokens || []);

    var irPre = document.getElementById('ir-pre');
    if (irPre) {
        try {
            irPre.textContent = d.ir ? JSON.stringify(d.ir, null, 2) : '--';
        } catch(e) {
            irPre.textContent = String(d.ir);
        }
    }
    var astPre = document.getElementById('ast-pre');
    if (astPre) astPre.textContent = d.ast ? JSON.stringify(d.ast, null, 2) : '--';

    updateMetrics(d);
}

function renderCompDetails(details) {
    if (!details || !details.pipeline) return;
    details.pipeline.forEach(function(step, i) {
        var el = document.getElementById('comp-step-' + (i + 1));
        if (!el) return;
        var statusEl = el.querySelector('.comp-status');
        var timeEl = el.querySelector('.comp-time');
        var st = step.status || 'ok';
        el.className = 'comp-step ' + (st === 'ok' ? 'ok' : st === 'err' ? 'err' : 'run');
        if (statusEl) {
            statusEl.className = 'comp-status ' + st;
            statusEl.textContent = st === 'ok' ? 'OK' : st === 'err' ? 'ERR' : '...';
        }
        if (timeEl) timeEl.textContent = step.time || '';
    });

    var content = document.getElementById('comp-detail-content');
    if (content) {
        var html = '';
        html += '<div class="detail-row"><span>Total</span><span>' + (details.total_time || '-') + '</span></div>';
        html += '<div class="detail-row"><span>Tokens</span><span>' + (details.tokens_count || '-') + '</span></div>';
        html += '<div class="detail-row"><span>AST</span><span>' + (details.ast_nodes || '-') + ' noeuds</span></div>';
        content.innerHTML = html;
    }
}

function renderSemanticPasses(report) {
    if (!report || !report.passes) return;
    report.passes.forEach(function(p, i) {
        var card = document.getElementById('pass-' + (i + 1));
        if (!card) return;
        var badge = card.querySelector('.pass-badge');
        var metricsEl = document.getElementById('pass-metrics-' + (i + 1));
        var errorsEl = document.getElementById('pass-errors-' + (i + 1));

        if (badge) {
            var st = p.status || 'ok';
            if (st === 'ok') { badge.className = 'pass-badge ok'; badge.textContent = 'OK'; }
            else if (st === 'err' || st === 'error') { badge.className = 'pass-badge err'; badge.textContent = 'ERR'; }
            else if (st === 'warning' || st === 'warn') { badge.className = 'pass-badge warn'; badge.textContent = 'WARN'; }
            else { badge.className = 'pass-badge pending'; badge.textContent = '--'; }
        }

        if (metricsEl && p.metrics) {
            var txt = Object.entries(p.metrics).map(function(kv) { return kv[0] + ': ' + kv[1]; }).join(' | ');
            metricsEl.textContent = txt;
        }

        if (errorsEl) {
            errorsEl.innerHTML = '';
            if (p.errors && p.errors.length) {
                p.errors.forEach(function(err) {
                    var div = document.createElement('div');
                    var sev = err.severity || 'error';
                    div.className = (sev === 'error' || sev === 'err') ? 'e-item' : 'w-item';
                    var loc = err.line ? 'L' + err.line + ': ' : '';
                    div.textContent = loc + (err.message || '');
                    errorsEl.appendChild(div);
                });
            }
        }
    });
}

function renderMap(graph) {
    var mapCanvas = document.getElementById('map-canvas');
    if (!mapCanvas) { log('Conteneur #map-canvas introuvable.', 'err'); return; }

    if (graphNet) {
        try { graphNet.destroy(); } catch(e) {}
        graphNet = null; graphDat = null;
    }
    mapCanvas.innerHTML = '';

    if (!graph || !graph.nodes || graph.nodes.length === 0) {
        mapCanvas.innerHTML = '<div class="empty-state"><p>Aucun noeud a afficher.</p><p>Compilez un fichier .ql avec des quetes.</p></div>';
        log('Graphe vide.', 'warn');
        return;
    }

    if (typeof vis === 'undefined' || !vis.Network) {
        log("ERREUR: vis.js non charge. Chargement depuis CDN...", 'warn');

        if (window._visLoading) return;
        window._visLoading = true;

        var script = document.createElement('script');
        script.src = 'https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js';
        script.onload = function() {
            window._visLoading = false;
            log('vis.js charge depuis CDN.', 'ok');
            renderMap(graph);
        };
        script.onerror = function() {
            window._visLoading = false;
            mapCanvas.innerHTML = '<div class="empty-state"><p>Impossible de charger vis.js.</p><p>Verifiez votre connexion internet.</p></div>';
            log("vis.js CDN inaccessible.", 'err');
        };
        document.head.appendChild(script);
        return;
    }

    try {
        edgeCounter = 0;
        var typeColors = { quest: '#9b59b6', item: '#e67e22', npc: '#1abc9c' };
        var typeShapes = { quest: 'box', item: 'diamond', npc: 'dot' };

        var nodesArr = graph.nodes.map(function(n) {
            var base = typeColors[n.type] || '#4a9eff';
            return {
                id: n.id,
                label: (n.label || n.id).substring(0, 20),
                color: { background: base, border: base, highlight: { background: base, border: '#fff' }, hover: { background: base, border: '#fff' } },
                shape: typeShapes[n.type] || 'box',
                font: { color: '#ffffff', size: 12, face: 'Segoe UI, sans-serif' },
                borderWidth: 2,
                type: n.type
            };
        });

        var edgesArr = graph.edges.map(function(e) {
            edgeCounter++;
            return {
                id: 'edge-' + edgeCounter,
                from: e.from,
                to: e.to,
                label: e.type || '',
                color: { color: e.color || '#4a9eff', opacity: 0.8 },
                arrows: { to: { enabled: true, scaleFactor: 0.8 } },
                font: { color: '#8a8aaa', size: 9 },
                dashes: e.dashes || false,
                smooth: { type: 'curvedCW', roundness: 0.2 }
            };
        });

        var nodes = new vis.DataSet(nodesArr);
        var edges = new vis.DataSet(edgesArr);
        graphDat = { nodes: nodes, edges: edges };

        var options = {
            layout: {
                hierarchical: {
                    direction: 'LR',
                    sortMethod: 'directed',
                    levelSeparation: 200,
                    nodeSpacing: 120,
                    treeSpacing: 150
                }
            },
            physics: { enabled: false },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true,
                dragNodes: true
            },
            nodes: { margin: 10 },
            edges: { smooth: { type: 'curvedCW', roundness: 0.2 } }
        };

        graphNet = new vis.Network(mapCanvas, graphDat, options);

        graphNet.once('stabilized', function() {
            graphNet.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        });

        log('Carte chargee: ' + nodesArr.length + ' noeuds, ' + edgesArr.length + ' liens.', 'ok');
    } catch (e) {
        log("Erreur graphe: " + e.message, 'err');
        console.error('Graph error:', e);
        mapCanvas.innerHTML = '<div class="empty-state"><p>Erreur lors du rendu du graphe:</p><p>' + esc(e.message) + '</p></div>';
    }
}

function applyGraphFilters() {
    if (!graphNet || !graphDat) return;
    var showQuest = document.getElementById('filter-quest');
    var showItem = document.getElementById('filter-item');
    var showNpc = document.getElementById('filter-npc');
    var showReward = document.getElementById('filter-reward');

    var types = {};
    if (showQuest && showQuest.checked) types.quest = true;
    if (showItem && showItem.checked) types.item = true;
    if (showNpc && showNpc.checked) types.npc = true;

    var nodes = graphDat.nodes.get();
    var edges = graphDat.edges.get();
    var visible = new Set();
    nodes.forEach(function(n) { if (types[n.type]) visible.add(n.id); });

    graphDat.nodes.update(nodes.map(function(n) {
        return { id: n.id, hidden: !types[n.type] };
    }));
    graphDat.edges.update(edges.map(function(e) {
        var isReward = e.label === 'reward' || e.label === 'cost';
        var showRew = showReward && showReward.checked;
        return {
            id: e.id,
            hidden: !(visible.has(e.from) && visible.has(e.to) && (!isReward || showRew))
        };
    }));
}

function renderSim() {
    var timeline = document.getElementById('sim-timeline');
    var detailTitle = document.getElementById('sim-detail-title');
    var detailBody = document.getElementById('sim-detail-body');
    var progressBar = document.getElementById('sim-progress-bar');

    if (!simData) {
        if (timeline) timeline.innerHTML = '<div class="empty-state"><p>Compilez pour simuler</p></div>';
        ['sim-gold','sim-xp','sim-item-count'].forEach(function(id) {
            var el = document.getElementById(id); if (el) el.textContent = '0';
        });
        if (detailTitle) detailTitle.textContent = 'Selectionnez une etape';
        if (detailBody) detailBody.innerHTML = '';
        if (progressBar) progressBar.style.width = '0%';
        return;
    }

    var order = simData.order || [];
    var history = simData.history || [];
    var inv = (simIndex >= 0 && history[simIndex]) ? history[simIndex].inventory_after : simData.inventory;

    var goldEl = document.getElementById('sim-gold');
    var xpEl = document.getElementById('sim-xp');
    var itemEl = document.getElementById('sim-item-count');
    if (goldEl) goldEl.textContent = (inv && inv.gold != null) ? Math.round(inv.gold) : 0;
    if (xpEl) xpEl.textContent = (inv && inv.xp != null) ? Math.round(inv.xp) : 0;
    if (itemEl) itemEl.textContent = Object.keys((inv && inv.items) || {}).length;
    if (progressBar) {
        progressBar.style.width = order.length > 0 ? (((simIndex + 1) / order.length) * 100) + '%' : '0%';
    }

    if (timeline) {
        timeline.innerHTML = '';
        if (order.length === 0) {
            timeline.innerHTML = '<div class="empty-state"><p>Aucune quete</p></div>';
        } else {
            order.forEach(function(qid, i) {
                var step = document.createElement('div');
                var cls = 'sim-step';
                if (i < simIndex) cls += ' completed';
                if (i === simIndex) cls += ' active';
                step.className = cls;
                step.innerHTML = '<div class="sim-step-num">' + (i + 1) + '</div><div class="sim-step-name">' + esc(qid) + '</div>';
                (function(idx) {
                    step.addEventListener('click', function() { simIndex = idx; renderSim(); });
                })(i);
                timeline.appendChild(step);
            });
        }
    }

    if (simIndex >= 0 && history[simIndex]) {
        var h = history[simIndex];
        if (detailTitle) detailTitle.textContent = h.title || h.quest || ('Etape ' + (simIndex + 1));
        var body = '';
        body += '<p><strong>Or:</strong> ' + Math.round((h.inventory_after && h.inventory_after.gold != null) ? h.inventory_after.gold : 0);
        body += '&nbsp;&nbsp;<strong>XP:</strong> ' + Math.round((h.inventory_after && h.inventory_after.xp != null) ? h.inventory_after.xp : 0) + '</p>';
        var items = (h.inventory_after && h.inventory_after.items) || {};
        var itemKeys = Object.keys(items);
        if (itemKeys.length > 0) {
            body += '<p><strong>Inventaire:</strong></p><ul>';
            itemKeys.forEach(function(k) { body += '<li>' + esc(k) + ' x' + items[k] + '</li>'; });
            body += '</ul>';
        }
        if (detailBody) detailBody.innerHTML = body;
    } else {
        if (detailTitle) detailTitle.textContent = 'Debut';
        var sg = (simData.inventory && simData.inventory.gold != null) ? simData.inventory.gold : 0;
        var sx = (simData.inventory && simData.inventory.xp != null) ? simData.inventory.xp : 0;
        if (detailBody) detailBody.innerHTML = '<p><strong>Or initial:</strong> ' + Math.round(sg) + '</p><p><strong>XP initial:</strong> ' + Math.round(sx) + '</p>';
    }
}

function renderTokens(tokens) {
    var tbody = document.getElementById('tok-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!tokens || !tokens.length) {
        tbody.innerHTML = '<tr><td colspan="4">Compilez pour afficher.</td></tr>';
        return;
    }
    tokens.forEach(function(t) {
        var tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (t.line || 0) + '</td><td>' + (t.col || 0) + '</td><td>' + esc(t.type) + '</td><td>' + esc(String(t.value !== undefined ? t.value : '')) + '</td>';
        tbody.appendChild(tr);
    });
}

function updateMetrics(d) {
    var ir = (d && d.ir) || {};
    var setM = function(id, val) { var el = document.getElementById(id); if (el) el.textContent = val; };
    setM('m-quests', countKeys(ir.quests));
    setM('m-items', countKeys(ir.items));
    setM('m-npcs', countKeys(ir.npcs));
    setM('m-errs', errs.length);
    setM('m-warns', warns.length);
    setM('m-tokens', (d.tokens || []).length);
    if (d.compilation_details) setM('m-time', d.compilation_details.total_time || '-');
}

function countKeys(obj) {
    if (!obj) return 0;
    if (Array.isArray(obj)) return obj.length;
    if (typeof obj === 'object') return Object.keys(obj).length;
    return 0;
}

function resetAll() {
    for (var i = 1; i <= 4; i++) {
        var step = document.getElementById('comp-step-' + i);
        if (step) {
            step.className = 'comp-step';
            var s = step.querySelector('.comp-status');
            if (s) { s.className = 'comp-status pending'; s.textContent = '--'; }
            var t = step.querySelector('.comp-time');
            if (t) t.textContent = '';
        }
        var card = document.getElementById('pass-' + i);
        if (card) {
            var b = card.querySelector('.pass-badge');
            if (b) { b.className = 'pass-badge pending'; b.textContent = '--'; }
            var m = document.getElementById('pass-metrics-' + i);
            if (m) m.innerHTML = '';
            var e = document.getElementById('pass-errors-' + i);
            if (e) e.innerHTML = '';
        }
    }
    var content = document.getElementById('comp-detail-content');
    if (content) content.innerHTML = 'Compilez pour voir les details.';

    simData = null; simIndex = -1; simPlaying = false;
    var playBtn = document.getElementById('sim-play');
    if (playBtn) playBtn.textContent = 'Play';
    if (simTimer) { clearTimeout(simTimer); simTimer = null; }
    renderSim();

    ['m-quests','m-items','m-npcs','m-errs','m-warns','m-tokens','m-time'].forEach(function(id) {
        var el = document.getElementById(id); if (el) el.textContent = '-';
    });

    var astPre = document.getElementById('ast-pre');
    var irPre = document.getElementById('ir-pre');
    if (astPre) astPre.textContent = 'Compilez pour afficher.';
    if (irPre) irPre.textContent = 'Compilez pour afficher.';

    var tokBody = document.getElementById('tok-body');
    if (tokBody) tokBody.innerHTML = 'Compilez pour afficher.';

    if (graphNet) {
        try { graphNet.destroy(); } catch(e) {}
        graphNet = null; graphDat = null;
    }
    var mapCanvas = document.getElementById('map-canvas');
    if (mapCanvas) mapCanvas.innerHTML = '';

    var statusDot = document.getElementById('status-dot');
    if (statusDot) statusDot.className = 'dot';
}

function log(msg, type) {
    var body = document.getElementById('console-body');
    if (!body) return;
    var line = document.createElement('div');
    line.className = 'c-line ' + (type || 'info');
    var now = new Date();
    var t = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0') + ':' + now.getSeconds().toString().padStart(2,'0');
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
    if (on) {
        btn.innerHTML = 'Compilation...';
        btn.disabled = true;
    } else {
        btn.innerHTML = 'Compiler';
        btn.disabled = false;
    }
}

function esc(t) {
    if (t == null) return '';
    var d = document.createElement('div');
    d.textContent = String(t);
    return d.innerHTML;
}

document.addEventListener('DOMContentLoaded', init);
})();
