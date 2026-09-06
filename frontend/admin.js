document.addEventListener("DOMContentLoaded", () => {
    // Elementos DOM
    const loginSection = document.getElementById("login-section");
    const dashboardSection = document.getElementById("dashboard-section");
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");
    const btnLogout = document.getElementById("btn-logout");

    // Stats Elements
    const statTotal = document.getElementById("stat-total");
    const statChollos = document.getElementById("stat-chollos");
    const statEstafas = document.getElementById("stat-estafas");
    const statAhorro = document.getElementById("stat-ahorro");

    // Filter Elements
    const searchInput = document.getElementById("search-input");
    const filterPlatform = document.getElementById("filter-platform");
    const filterVerdict = document.getElementById("filter-verdict");
    const filterSort = document.getElementById("filter-sort");
    const btnRefresh = document.getElementById("btn-refresh");
    const btnExportCsv = document.getElementById("btn-export-csv");

    // Modal Benchmarks
    const modalBenchmarks = document.getElementById("modal-benchmarks");
    const btnOpenBenchmarks = document.getElementById("btn-open-benchmarks");
    const btnCloseBenchmarks = document.getElementById("btn-close-benchmarks");
    const benchmarkForm = document.getElementById("benchmark-form");
    const benchmarksList = document.getElementById("benchmarks-list");

    // Table
    const tableBody = document.getElementById("admin-table-body");
    const tableCountLabel = document.getElementById("table-count-label");

    // Tabs & Views
    const tabBtnMultiweb = document.getElementById("tab-btn-multiweb");
    const tabBtnScans = document.getElementById("tab-btn-scans");
    const tabBtnRaw = document.getElementById("tab-btn-raw");
    const tabBtnHarvester = document.getElementById("tab-btn-harvester");
    const tabBtnAlerts = document.getElementById("tab-btn-alerts");
    const tabBadgeScans = document.getElementById("tab-badge-scans");
    const tabBadgeRaw = document.getElementById("tab-badge-raw");
    const viewMultiweb = document.getElementById("view-multiweb");
    const viewScans = document.getElementById("view-scans");
    const viewRaw = document.getElementById("view-raw");
    const viewHarvester = document.getElementById("view-harvester");
    const viewAlerts = document.getElementById("view-alerts");
    const btnMultiwebRefresh = document.getElementById("btn-multiweb-refresh");
    const btnScannerRefresh = document.getElementById("btn-scanner-refresh");

    // Scanner & Telegram Elements
    const tgStatusBadge = document.getElementById("tg-status-badge");
    const tgTokenLabel = document.getElementById("tg-token-label");
    const tgChatLabel = document.getElementById("tg-chat-label");
    const btnTestTelegram = document.getElementById("btn-test-telegram");
    const tgTestFeedback = document.getElementById("tg-test-feedback");
    const tgGuideBox = document.getElementById("tg-guide-box");
    const scannerStatusBadge = document.getElementById("scanner-status-badge");
    const scannerMetricCycles = document.getElementById("scanner-metric-cycles");
    const scannerMetricDeals = document.getElementById("scanner-metric-deals");
    const scannerLastScan = document.getElementById("scanner-last-scan");
    const scannerNextScan = document.getElementById("scanner-next-scan");
    const btnScannerToggle = document.getElementById("btn-scanner-toggle");
    const btnScannerRunOnce = document.getElementById("btn-scanner-run-once");
    const scannerActionFeedback = document.getElementById("scanner-action-feedback");
    const scannerConfigForm = document.getElementById("scanner-config-form");
    const cfgInterval = document.getElementById("cfg-interval");
    const cfgMinScore = document.getElementById("cfg-min-score");
    const cfgMinSavings = document.getElementById("cfg-min-savings");
    const cfgKeywords = document.getElementById("cfg-keywords");
    const cfgFeedback = document.getElementById("cfg-feedback");
    const scannerHistoryBody = document.getElementById("scanner-history-body");
    const scannerHistoryCount = document.getElementById("scanner-history-count");

    // Raw Listings Elements
    const rawTableBody = document.getElementById("raw-table-body");
    const rawTableCountLabel = document.getElementById("raw-table-count-label");
    const rawSearchInput = document.getElementById("raw-search-input");
    const rawFilterPlatform = document.getElementById("raw-filter-platform");
    const btnRawRefresh = document.getElementById("btn-raw-refresh");
    const rawStatTotal = document.getElementById("raw-stat-total");
    const rawStatMedian = document.getElementById("raw-stat-median");
    const rawStatRange = document.getElementById("raw-stat-range");
    const rawStatAvg = document.getElementById("raw-stat-avg");

    // Harvester Elements
    const harvesterForm = document.getElementById("harvester-form");
    const harvesterKeyword = document.getElementById("harvester-keyword");
    const harvesterPlatform = document.getElementById("harvester-platform");
    const harvesterLimit = document.getElementById("harvester-limit");
    const harvesterOnlySpain = document.getElementById("harvester-only-spain");
    const btnRunHarvest = document.getElementById("btn-run-harvest");
    const harvesterLoading = document.getElementById("harvester-loading");
    const harvesterResults = document.getElementById("harvester-results");
    const harvesterTableBody = document.getElementById("harvester-table-body");
    const hMetricValid = document.getElementById("h-metric-valid");
    const hMetricMedian = document.getElementById("h-metric-median");
    const hMetricRange = document.getElementById("h-metric-range");
    const hMetricNoise = document.getElementById("h-metric-noise");
    const btnSaveHarvestBenchmark = document.getElementById("btn-save-harvest-benchmark");

    // Estado en memoria
    let rawScans = [];
    let filteredScans = [];
    let lastHarvestData = null;

    // 1. Comprobar si ya existe sesión iniciada
    checkAuth();

    function checkAuth() {
        const token = sessionStorage.getItem("admin_token");
        if (token) {
            loginSection.classList.add("hidden");
            dashboardSection.classList.remove("hidden");
            btnLogout.classList.remove("hidden");
            loadDashboard();
        } else {
            loginSection.classList.remove("hidden");
            dashboardSection.classList.add("hidden");
            btnLogout.classList.add("hidden");
        }
    }

    // 2. Manejo de Login
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        loginError.style.display = "none";

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        try {
            const res = await fetch("/api/admin/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                sessionStorage.setItem("admin_token", data.token);
                checkAuth();
            } else {
                loginError.textContent = data.detail || "Credenciales incorrectas";
                loginError.style.display = "block";
            }
        } catch (err) {
            loginError.textContent = "Error de conexión con el servidor";
            loginError.style.display = "block";
        }
    });

    // 3. Cerrar sesión
    btnLogout.addEventListener("click", () => {
        sessionStorage.removeItem("admin_token");
        checkAuth();
    });

    // 4. Cargar datos del dashboard
    async function loadDashboard() {
        const token = sessionStorage.getItem("admin_token");
        try {
            // Cargar estadísticas
            const statsRes = await fetch("/api/admin/stats", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (statsRes.ok) {
                const stats = await statsRes.json();
                statTotal.textContent = stats.total_scans;
                statChollos.textContent = stats.bargains_count;
                statEstafas.textContent = stats.scams_flagged;
                statAhorro.textContent = `${stats.total_savings.toFixed(0)} €`;
            } else if (statsRes.status === 401 || statsRes.status === 403) {
                sessionStorage.removeItem("admin_token");
                checkAuth();
                return;
            }

            // Cargar listado completo de productos
            const dataRes = await fetch("/api/admin/data?limit=300", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (dataRes.ok) {
                const data = await dataRes.json();
                rawScans = data.scans || [];
                if (tabBadgeScans) tabBadgeScans.textContent = rawScans.length;
                applyFilters();
            }
            // Precargar conteo de raw listings y monitor multiweb
            loadRawListings();
            loadPlatformStats();
        } catch (err) {
            console.error("Error al cargar datos de admin:", err);
        }
    }

    // 5. Aplicar filtros y ordenación
    function applyFilters() {
        const query = searchInput.value.toLowerCase().trim();
        const platform = filterPlatform ? filterPlatform.value : "all";
        const verdict = filterVerdict.value;
        const sort = filterSort.value;

        // Filtrado
        filteredScans = rawScans.filter(item => {
            // Filtro de plataforma
            if (platform !== "all") {
                const itemPlat = (item.platform || "wallapop").toLowerCase();
                if (itemPlat !== platform) return false;
            }

            // Búsqueda de texto
            const matchQuery = !query || 
                (item.title && item.title.toLowerCase().includes(query)) ||
                (item.normalized_product && item.normalized_product.toLowerCase().includes(query)) ||
                (item.seller_name && item.seller_name.toLowerCase().includes(query));

            if (!matchQuery) return false;

            // Filtro de veredicto
            const score = parseFloat(item.score || 0);
            const risk = (item.risk_level || "").toUpperCase();

            if (verdict === "chollo" && score < 7.5) return false;
            if (verdict === "justo" && (score < 5.0 || score >= 7.5)) return false;
            if (verdict === "caro" && score >= 5.0) return false;
            if (verdict === "estafa" && risk !== "ALTO" && !item.verdict?.includes("Estafa")) return false;

            return true;
        });

        // Ordenación
        filteredScans.sort((a, b) => {
            if (sort === "date-desc") return (b.id || 0) - (a.id || 0);
            if (sort === "score-desc") return (b.score || 0) - (a.score || 0);
            if (sort === "score-asc") return (a.score || 0) - (b.score || 0);
            if (sort === "price-asc") return (a.price || 0) - (b.price || 0);
            if (sort === "price-desc") return (b.price || 0) - (a.price || 0);
            if (sort === "savings-desc") return (b.savings || 0) - (a.savings || 0);
            return 0;
        });

        renderTable();
    }

    // 6. Eliminar producto de Supabase
    window.deleteScan = async function(id, title) {
        if (!confirm(`¿Estás seguro de eliminar este registro de la base de datos?\n"${title}"`)) {
            return;
        }

        const token = sessionStorage.getItem("admin_token");
        try {
            const res = await fetch(`/api/admin/scan/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.ok) {
                rawScans = rawScans.filter(s => s.id !== id);
                applyFilters();
                // Actualizar contador total
                statTotal.textContent = rawScans.length;
            } else {
                alert("No se pudo eliminar el registro.");
            }
        } catch (e) {
            alert("Error de conexión al eliminar.");
        }
    };

    function escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return "";
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // 7. Renderizar tabla en pantalla
    function renderTable() {
        tableBody.innerHTML = "";
        tableCountLabel.textContent = `Mostrando ${filteredScans.length} de ${rawScans.length} productos`;

        if (filteredScans.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 36px; color: var(--text-muted);">
                        No se encontraron productos que coincidan con los filtros aplicados.
                    </td>
                </tr>
            `;
            return;
        }

        filteredScans.forEach(item => {
            const tr = document.createElement("tr");

            // Formato de Score Badge
            const score = parseFloat(item.score || 0).toFixed(1);
            let scoreBg = "rgba(16, 185, 129, 0.15)";
            let scoreColor = "#34D399";
            if (score < 3.5 || item.risk_level === "ALTO") {
                scoreBg = "rgba(239, 68, 68, 0.2)";
                scoreColor = "#F87171";
            } else if (score < 7.2) {
                scoreBg = "rgba(245, 158, 11, 0.15)";
                scoreColor = "#FBBF24";
            }

            // Formato de Ahorro
            const savings = parseFloat(item.savings || 0);
            const savingsPct = Math.round(item.savings_pct || 0);
            const savingsHtml = savings > 0 
                ? `<span class="savings-pos">+${savings.toFixed(0)} € (-${savingsPct}%)</span>`
                : `<span class="savings-neg">${savings.toFixed(0)} € (+${Math.abs(savingsPct)}%)</span>`;

            // Formato de Riesgo
            const riskClass = escapeHtml((item.risk_level || "BAJO").toLowerCase());
            const platformName = escapeHtml((item.platform || "wallapop").toUpperCase());
            const safeTitle = escapeHtml(item.title || "Sin título");
            const safeProduct = escapeHtml(item.normalized_product || "General");
            const safeUrl = escapeHtml(item.url || "#");
            const safeId = parseInt(item.id, 10) || 0;

            tr.innerHTML = `
                <td>
                    <span class="score-pill" style="background: ${scoreBg}; color: ${scoreColor};">
                        ★ ${score}
                    </span>
                </td>
                <td class="item-title-cell">
                    <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="item-title-link" title="${safeTitle}">
                        ${safeTitle}
                    </a>
                    <span class="item-subtext">📦 ${safeProduct} · <strong>${platformName}</strong></span>
                </td>
                <td>
                    <div class="price-current">${parseFloat(item.price || 0).toFixed(0)} €</div>
                </td>
                <td>
                    <div class="price-bench">${item.market_price ? parseFloat(item.market_price).toFixed(0) + ' €' : '-'}</div>
                </td>
                <td>${savingsHtml}</td>
                <td>
                    <div style="font-weight: 600;">⭐ ${parseFloat(item.seller_rating || 5.0).toFixed(1)}</div>
                    <div class="item-subtext">${parseInt(item.seller_reviews || 0, 10)} reviews</div>
                </td>
                <td>
                    <span style="font-size: 0.8rem;">${item.has_shipping ? '✅ Disponible' : '🚫 En mano'}</span>
                </td>
                <td>
                    <span class="risk-badge risk-${riskClass}">${escapeHtml(item.risk_level || 'NORMAL')}</span>
                </td>
                <td style="white-space: nowrap;">
                    <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="btn-external" title="Abrir anuncio original">
                        ↗ Ver
                    </a>
                    <button onclick="deleteScan(${safeId}, '${safeTitle.replace(/'/g, "\\'")}')" class="btn-delete" title="Eliminar de la base de datos">
                        🗑️
                    </button>
                </td>
            `;

            tableBody.appendChild(tr);
        });
    }

    // 8. Eventos de los filtros
    searchInput.addEventListener("input", applyFilters);
    if (filterPlatform) filterPlatform.addEventListener("change", applyFilters);
    filterVerdict.addEventListener("change", applyFilters);
    filterSort.addEventListener("change", applyFilters);
    btnRefresh.addEventListener("click", loadDashboard);

    // 9. Exportar a CSV
    btnExportCsv.addEventListener("click", () => {
        if (filteredScans.length === 0) {
            alert("No hay datos para exportar con los filtros actuales.");
            return;
        }

        const headers = ["ID", "Plataforma", "Título", "Precio", "Mediana", "Ahorro EUR", "Ahorro PCT", "Score", "Veredicto", "Riesgo", "Reviews Vendedor", "URL"];
        const rows = filteredScans.map(s => [
            s.id || "",
            s.platform || "wallapop",
            `"${(s.title || "").replace(/"/g, '""')}"`,
            s.price || 0,
            s.market_price || 0,
            s.savings || 0,
            s.savings_pct || 0,
            s.score || 0,
            `"${s.verdict || ''}"`,
            s.risk_level || "NORMAL",
            s.seller_reviews || 0,
            s.url || ""
        ]);

        const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `gangacheck_bbdd_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // 10. Modal de Benchmarks
    if (btnOpenBenchmarks) {
        btnOpenBenchmarks.addEventListener("click", () => {
            modalBenchmarks.classList.remove("hidden");
            loadBenchmarks();
        });
    }

    if (btnCloseBenchmarks) {
        btnCloseBenchmarks.addEventListener("click", () => {
            modalBenchmarks.classList.add("hidden");
        });
    }

    async function loadBenchmarks() {
        const token = sessionStorage.getItem("admin_token");
        try {
            const res = await fetch("/api/admin/benchmarks", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                const list = data.benchmarks || [];
                benchmarksList.innerHTML = "";
                list.forEach(b => {
                    const row = document.createElement("div");
                    row.style.padding = "6px 8px";
                    row.style.borderBottom = "1px solid rgba(255,255,255,0.06)";
                    row.style.display = "flex";
                    row.style.justifyContent = "space-between";
                    row.innerHTML = `
                        <span><strong>${b.display_name}</strong> <span style="color:var(--text-muted);">(${b.category})</span></span>
                        <span style="color:var(--accent-green); font-weight:700;">${b.median_price} €</span>
                    `;
                    benchmarksList.appendChild(row);
                });
            }
        } catch (e) {
            benchmarksList.innerHTML = "<p style='color:var(--accent-red);'>Error al cargar benchmarks</p>";
        }
    }

    if (benchmarkForm) {
        benchmarkForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const token = sessionStorage.getItem("admin_token");
            const newBm = {
                display_name: document.getElementById("bm-display").value.trim(),
                product_key: document.getElementById("bm-key").value.trim(),
                category: document.getElementById("bm-cat").value.trim(),
                median_price: parseFloat(document.getElementById("bm-median").value),
                min_normal_price: parseFloat(document.getElementById("bm-min").value),
                max_normal_price: parseFloat(document.getElementById("bm-median").value) * 1.25
            };

            try {
                const res = await fetch("/api/admin/benchmarks", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(newBm)
                });
                if (res.ok) {
                    alert("¡Modelo guardado correctamente en Supabase!");
                    benchmarkForm.reset();
                    loadBenchmarks();
                } else {
                    alert("No se pudo guardar el modelo.");
                }
            } catch (err) {
                alert("Error de conexión.");
            }
        });
    }

    // ==========================================
    // ==========================================
    // 7. GESTIÓN DE PESTAÑAS (TABS)
    // ==========================================
    function switchTab(tabId) {
        if (tabBtnMultiweb) tabBtnMultiweb.classList.remove("active");
        if (tabBtnScans) tabBtnScans.classList.remove("active");
        if (tabBtnRaw) tabBtnRaw.classList.remove("active");
        if (tabBtnHarvester) tabBtnHarvester.classList.remove("active");
        if (tabBtnAlerts) tabBtnAlerts.classList.remove("active");

        if (viewMultiweb) viewMultiweb.classList.add("hidden");
        if (viewScans) viewScans.classList.add("hidden");
        if (viewRaw) viewRaw.classList.add("hidden");
        if (viewHarvester) viewHarvester.classList.add("hidden");
        if (viewAlerts) viewAlerts.classList.add("hidden");

        if (tabId === "multiweb") {
            if (tabBtnMultiweb) tabBtnMultiweb.classList.add("active");
            if (viewMultiweb) viewMultiweb.classList.remove("hidden");
            loadPlatformStats();
        } else if (tabId === "scans") {
            if (tabBtnScans) tabBtnScans.classList.add("active");
            if (viewScans) viewScans.classList.remove("hidden");
        } else if (tabId === "raw") {
            if (tabBtnRaw) tabBtnRaw.classList.add("active");
            if (viewRaw) viewRaw.classList.remove("hidden");
            loadRawListings();
        } else if (tabId === "harvester") {
            if (tabBtnHarvester) tabBtnHarvester.classList.add("active");
            if (viewHarvester) viewHarvester.classList.remove("hidden");
        } else if (tabId === "alerts") {
            if (tabBtnAlerts) tabBtnAlerts.classList.add("active");
            if (viewAlerts) viewAlerts.classList.remove("hidden");
            loadScannerStatus();
        }
    }

    if (tabBtnMultiweb) tabBtnMultiweb.addEventListener("click", () => switchTab("multiweb"));
    if (tabBtnScans) tabBtnScans.addEventListener("click", () => switchTab("scans"));
    if (tabBtnRaw) tabBtnRaw.addEventListener("click", () => switchTab("raw"));
    if (tabBtnHarvester) tabBtnHarvester.addEventListener("click", () => switchTab("harvester"));
    if (tabBtnAlerts) tabBtnAlerts.addEventListener("click", () => switchTab("alerts"));

    // ==========================================
    // 7.1 MONITOR MULTI-WEB (DASHBOARD COMPARATIVO)
    // ==========================================
    async function loadPlatformStats() {
        const token = sessionStorage.getItem("admin_token");
        if (!token) return;

        try {
            const res = await fetch("/api/admin/platform-stats", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) return;
            const data = await res.json();
            const platforms = data.platforms || {};
            const totalDb = data.total_database_items || 0;
            const totalScans = data.total_scans || 0;
            const totalRaw = data.total_raw || 0;

            const totalCounter = document.getElementById("multiweb-total-counter");
            if (totalCounter) {
                totalCounter.textContent = `${totalDb} registros totales (${totalScans} escaneos + ${totalRaw} catálogo)`;
            }

            const pKeys = ["wallapop", "vinted", "milanuncios"];
            pKeys.forEach(p => {
                const pData = platforms[p] || {};
                const sharePct = pData.share_pct || 0;
                const totalItems = pData.total_items || 0;

                // Barra de progreso
                const bar = document.getElementById(`share-bar-${p}`);
                if (bar) bar.style.width = `${Math.max(sharePct, 2)}%`;

                // Etiqueta leyenda
                const lbl = document.getElementById(`share-lbl-${p}`);
                if (lbl) lbl.textContent = `${sharePct}% (${totalItems})`;

                // Métricas de tarjetas
                const elTotal = document.getElementById(`mw-total-${p}`);
                if (elTotal) elTotal.textContent = totalItems;

                const elMedian = document.getElementById(`mw-median-${p}`);
                if (elMedian) elMedian.textContent = `${pData.median_price || 0} €`;

                const elChollos = document.getElementById(`mw-chollos-${p}`);
                if (elChollos) elChollos.textContent = pData.chollos_count || 0;

                const elRisks = document.getElementById(`mw-risks-${p}`);
                if (elRisks) elRisks.textContent = pData.risks_count || 0;

                const elScans = document.getElementById(`mw-scans-${p}`);
                if (elScans) elScans.textContent = pData.scans_count || 0;

                const elRaw = document.getElementById(`mw-raw-${p}`);
                if (elRaw) elRaw.textContent = pData.raw_count || 0;

                // Celdas de tabla comparativa
                const tdTotal = document.getElementById(`td-total-${p}`);
                if (tdTotal) tdTotal.textContent = totalItems;

                const tdShare = document.getElementById(`td-share-${p}`);
                if (tdShare) tdShare.textContent = `${sharePct}%`;

                const tdMedian = document.getElementById(`td-median-${p}`);
                if (tdMedian) tdMedian.textContent = `${pData.median_price || 0} €`;

                const tdChollos = document.getElementById(`td-chollos-${p}`);
                if (tdChollos) tdChollos.textContent = pData.chollos_count || 0;

                const tdRisks = document.getElementById(`td-risks-${p}`);
                if (tdRisks) tdRisks.textContent = pData.risks_count || 0;
            });
        } catch (err) {
            console.error("Error al cargar estadísticas multiweb:", err);
        }
    }

    if (btnMultiwebRefresh) {
        btnMultiwebRefresh.addEventListener("click", () => {
            btnMultiwebRefresh.textContent = "⏳ Actualizando...";
            loadPlatformStats().finally(() => {
                setTimeout(() => {
                    btnMultiwebRefresh.textContent = "🔄 Actualizar Métricas";
                }, 400);
            });
        });
    }

    // Botones de acción rápida desde las tarjetas de web
    const btnQuickHarvestMilanuncios = document.getElementById("btn-quick-harvest-milanuncios");
    if (btnQuickHarvestMilanuncios) {
        btnQuickHarvestMilanuncios.addEventListener("click", () => {
            switchTab("harvester");
            if (harvesterPlatform) harvesterPlatform.value = "milanuncios";
            if (harvesterKeyword) harvesterKeyword.focus();
        });
    }

    const btnQuickRawMilanuncios = document.getElementById("btn-quick-raw-milanuncios");
    if (btnQuickRawMilanuncios) {
        btnQuickRawMilanuncios.addEventListener("click", () => {
            switchTab("raw");
            if (rawFilterPlatform) {
                rawFilterPlatform.value = "milanuncios";
                loadRawListings();
            }
        });
    }

    const btnQuickHarvestVinted = document.getElementById("btn-quick-harvest-vinted");
    if (btnQuickHarvestVinted) {
        btnQuickHarvestVinted.addEventListener("click", () => {
            switchTab("harvester");
            if (harvesterPlatform) harvesterPlatform.value = "vinted";
            if (harvesterKeyword) harvesterKeyword.focus();
        });
    }

    const btnQuickRawVinted = document.getElementById("btn-quick-raw-vinted");
    if (btnQuickRawVinted) {
        btnQuickRawVinted.addEventListener("click", () => {
            switchTab("raw");
            if (rawFilterPlatform) {
                rawFilterPlatform.value = "vinted";
                loadRawListings();
            }
        });
    }

    const btnQuickScansWallapop = document.getElementById("btn-quick-scans-wallapop");
    if (btnQuickScansWallapop) {
        btnQuickScansWallapop.addEventListener("click", () => {
            switchTab("scans");
            if (filterPlatform) {
                filterPlatform.value = "wallapop";
                applyFilters();
            }
        });
    }

    // ==========================================
    // 8. EXPLORADOR DE BBDD DE MERCADO (RAW LISTINGS)
    // ==========================================
    async function loadRawListings() {
        const token = sessionStorage.getItem("admin_token");
        if (!token) return;
        const query = rawSearchInput ? rawSearchInput.value.trim() : "";
        const plat = rawFilterPlatform ? rawFilterPlatform.value : "all";

        try {
            const url = `/api/admin/raw-listings?keyword=${encodeURIComponent(query)}&platform=${encodeURIComponent(plat)}&limit=200`;
            const res = await fetch(url, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) return;
            const data = await res.json();
            const items = data.listings || [];
            const stats = data.stats || {};

            if (tabBadgeRaw) tabBadgeRaw.textContent = stats.total_items || items.length;
            if (rawStatTotal) rawStatTotal.textContent = stats.total_items || items.length;
            if (rawStatMedian) rawStatMedian.textContent = `${stats.median_price || 0} €`;
            if (rawStatRange) rawStatRange.textContent = `${stats.min_price || 0} € - ${stats.max_price || 0} €`;
            if (rawStatAvg) rawStatAvg.textContent = `${stats.avg_price || 0} €`;
            if (rawTableCountLabel) rawTableCountLabel.textContent = `Mostrando ${items.length} anuncios`;

            renderRawTable(items);
        } catch (err) {
            console.error("Error al cargar raw listings:", err);
        }
    }

    if (rawSearchInput) {
        let debounceTimeout;
        rawSearchInput.addEventListener("input", () => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(loadRawListings, 300);
        });
    }

    if (rawFilterPlatform) {
        rawFilterPlatform.addEventListener("change", loadRawListings);
    }

    if (btnRawRefresh) {
        btnRawRefresh.addEventListener("click", loadRawListings);
    }

    function renderRawTable(items) {
        if (!rawTableBody) return;
        rawTableBody.innerHTML = "";
        if (items.length === 0) {
            rawTableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 32px; color: var(--text-muted);">No se encontraron anuncios en el histórico. Usa el <strong>Recolector en Vivo</strong> para rastrear ofertas reales.</td></tr>`;
            return;
        }

        items.forEach(item => {
            const tr = document.createElement("tr");
            const thumb = item.image_url ? 
                `<img src="${escapeHtml(item.image_url)}" class="table-thumb" alt="Foto" onerror="this.outerHTML='<div class=\\'thumb-fallback\\'>📦</div>'">` :
                `<div class="thumb-fallback">📦</div>`;
            
            const platClass = (item.platform || "vinted").toLowerCase();
            const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString("es-ES", { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : "Reciente";

            tr.innerHTML = `
                <td>${thumb}</td>
                <td class="item-title-cell">
                    <a href="${escapeHtml(item.url)}" target="_blank" class="item-title-link">${escapeHtml(item.title)}</a>
                    <span class="item-subtext">Búsqueda: ${escapeHtml(item.keyword || "—")}</span>
                </td>
                <td><span class="badge-platform ${platClass}">${escapeHtml(item.platform)}</span></td>
                <td><span class="price-current">${item.price.toFixed(2)} €</span></td>
                <td>
                    <div>${escapeHtml(item.seller_name || "Vendedor")}</div>
                    <div class="item-subtext">⭐ ${item.seller_reviews || 0} reviews</div>
                </td>
                <td>${item.has_shipping ? '<span class="risk-badge risk-bajo">✓ Envío</span>' : '<span style="color:var(--text-muted);">—</span>'}</td>
                <td style="font-size: 0.8rem; color: var(--text-muted);">${dateStr}</td>
                <td><a href="${escapeHtml(item.url)}" target="_blank" class="btn-external">↗ Ver Anuncio</a></td>
                <td>
                    <button class="btn-ghost btn-delete-raw" data-id="${escapeHtml(item.id)}" title="Eliminar registro" style="color: #F87171; border-color: rgba(239, 68, 68, 0.2);">
                        🗑️
                    </button>
                </td>
            `;
            rawTableBody.appendChild(tr);
        });

        // Eventos de borrado de fila individual
        rawTableBody.querySelectorAll(".btn-delete-raw").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const id = e.currentTarget.getAttribute("data-id");
                if (confirm("¿Deseas eliminar este registro de la base de datos?")) {
                    const token = sessionStorage.getItem("admin_token");
                    const res = await fetch(`/api/admin/raw-listing/${encodeURIComponent(id)}`, {
                        method: "DELETE",
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    if (res.ok) {
                        loadRawListings();
                    }
                }
            });
        });
    }

    // ==========================================
    // 9. RECOLECTOR DE MERCADO EN VIVO (HARVESTER)
    // ==========================================
    if (harvesterForm) {
        harvesterForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const kw = harvesterKeyword.value.trim();
            if (!kw) return;
            const plat = harvesterPlatform.value;
            const lim = parseInt(harvesterLimit.value, 10);
            runHarvest(kw, plat, lim);
        });
    }

    // Botones de búsqueda rápida (chips)
    document.querySelectorAll(".quick-tags .tag-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const kw = btn.getAttribute("data-kw");
            if (harvesterKeyword) harvesterKeyword.value = kw;
            runHarvest(kw, "all", 50);
        });
    });

    async function runHarvest(keyword, platform, limit) {
        const token = sessionStorage.getItem("admin_token");
        if (!token) return;

        harvesterLoading.classList.remove("hidden");
        harvesterResults.classList.add("hidden");
        btnRunHarvest.disabled = true;

        try {
            const res = await fetch("/api/admin/harvest", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    keyword,
                    platform,
                    limit,
                    only_spain: harvesterOnlySpain ? harvesterOnlySpain.checked : true
                })
            });

            const data = await res.json();
            harvesterLoading.classList.add("hidden");
            btnRunHarvest.disabled = false;

            if (res.ok && data.success) {
                lastHarvestData = data;
                harvesterResults.classList.remove("hidden");

                const m = data.metrics || {};
                hMetricValid.textContent = m.total_valid || 0;
                hMetricMedian.textContent = `${m.median_price || 0} €`;
                hMetricRange.textContent = `${m.min_normal_price || 0} € - ${m.max_normal_price || 0} €`;
                hMetricNoise.textContent = data.noise_discarded || 0;

                // Renderizar tabla de resultados recién recolectados
                renderHarvesterTable(data.listings || []);

                // Actualizar contador del tab de raw
                loadRawListings();
            } else {
                alert(data.detail || "Hubo un error al rastrear el mercado.");
            }
        } catch (err) {
            harvesterLoading.classList.add("hidden");
            btnRunHarvest.disabled = false;
            alert("Error de conexión al rastrear el mercado.");
        }
    }

    function renderHarvesterTable(listings) {
        if (!harvesterTableBody) return;
        harvesterTableBody.innerHTML = "";
        if (listings.length === 0) {
            harvesterTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">No se obtuvieron anuncios válidos tras descartar ruido.</td></tr>`;
            return;
        }

        listings.forEach(it => {
            const tr = document.createElement("tr");
            const thumb = it.image_url ? 
                `<img src="${escapeHtml(it.image_url)}" class="table-thumb" alt="Foto" onerror="this.outerHTML='<div class=\\'thumb-fallback\\'>📦</div>'">` :
                `<div class="thumb-fallback">📦</div>`;

            const platClass = (it.platform || "vinted").toLowerCase();

            tr.innerHTML = `
                <td>${thumb}</td>
                <td class="item-title-cell">
                    <a href="${escapeHtml(it.url)}" target="_blank" class="item-title-link">${escapeHtml(it.title)}</a>
                </td>
                <td><span class="badge-platform ${platClass}">${escapeHtml(it.platform)}</span></td>
                <td><span class="price-current">${it.price.toFixed(2)} €</span></td>
                <td>${escapeHtml(it.seller_name || "Vendedor")}</td>
                <td>${it.has_shipping ? '<span class="risk-badge risk-bajo">✓ Envío</span>' : '<span style="color:var(--text-muted);">—</span>'}</td>
                <td><a href="${escapeHtml(it.url)}" target="_blank" class="btn-external">↗ Ver Anuncio</a></td>
            `;
            harvesterTableBody.appendChild(tr);
        });
    }

    // 1-Click Guardar como Benchmark Oficial en Supabase
    if (btnSaveHarvestBenchmark) {
        btnSaveHarvestBenchmark.addEventListener("click", async () => {
            if (!lastHarvestData || !lastHarvestData.metrics) {
                alert("Primero debes realizar una búsqueda.");
                return;
            }

            const token = sessionStorage.getItem("admin_token");
            const m = lastHarvestData.metrics;
            const kw = lastHarvestData.keyword;
            const slug = kw.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");

            const payload = {
                product_key: slug,
                display_name: kw,
                median_price: m.median_price,
                min_normal_price: m.min_normal_price,
                max_normal_price: m.max_normal_price,
                category: "Mercado Recolectado"
            };

            try {
                const res = await fetch("/api/admin/save-benchmark-from-harvest", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    btnSaveHarvestBenchmark.textContent = "✅ ¡Benchmark Guardado en Supabase!";
                    btnSaveHarvestBenchmark.style.background = "var(--accent-green)";
                    setTimeout(() => {
                        btnSaveHarvestBenchmark.textContent = "🏷️ Guardar como Benchmark Oficial";
                        btnSaveHarvestBenchmark.style.background = "";
                    }, 3500);
                    loadBenchmarks();
                } else {
                    alert("No se pudo guardar el benchmark.");
                }
            } catch (err) {
                alert("Error de conexión al guardar benchmark.");
            }
        });
    }

    // ==========================================
    // 7.4 ALERTAS EN TIEMPO REAL & AUTO-SCANNER
    // ==========================================
    async function loadScannerStatus() {
        const token = sessionStorage.getItem("admin_token");
        if (!token) return;

        try {
            const res = await fetch("/api/admin/scanner/status", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!res.ok) return;

            const data = await res.json();

            // 1. Estado Telegram
            if (tgStatusBadge) {
                if (data.telegram_configured) {
                    tgStatusBadge.textContent = "🟢 Conectado";
                    tgStatusBadge.className = "badge-status status-online";
                    if (tgTokenLabel) tgTokenLabel.textContent = "•••• Configurado";
                    if (tgChatLabel) tgChatLabel.textContent = "•••• Conectado";
                    if (tgGuideBox) tgGuideBox.style.display = "none";
                } else {
                    tgStatusBadge.textContent = "🟡 Sin Configurar";
                    tgStatusBadge.className = "badge-status status-emulated";
                    if (tgTokenLabel) tgTokenLabel.textContent = "No definido en .env/Render";
                    if (tgChatLabel) tgChatLabel.textContent = "No definido en .env/Render";
                    if (tgGuideBox) tgGuideBox.style.display = "block";
                }
            }

            // 2. Estado Scanner
            if (scannerStatusBadge) {
                if (data.is_running) {
                    scannerStatusBadge.textContent = "🟢 En Ejecución";
                    scannerStatusBadge.className = "badge-status status-online";
                    if (btnScannerToggle) {
                        btnScannerToggle.textContent = "⏸️ Pausar Scanner";
                        btnScannerToggle.style.background = "rgba(239, 68, 68, 0.2)";
                        btnScannerToggle.style.color = "#F87171";
                        btnScannerToggle.style.borderColor = "rgba(239, 68, 68, 0.4)";
                    }
                } else {
                    scannerStatusBadge.textContent = "⏸️ En Pausa";
                    scannerStatusBadge.className = "badge-status status-offline";
                    if (btnScannerToggle) {
                        btnScannerToggle.textContent = "▶️ Iniciar Scanner";
                        btnScannerToggle.style.background = "var(--accent-blue)";
                        btnScannerToggle.style.color = "#fff";
                        btnScannerToggle.style.borderColor = "transparent";
                    }
                }
            }

            // 3. Métricas
            if (scannerMetricCycles) scannerMetricCycles.textContent = data.total_scans_completed || 0;
            if (scannerMetricDeals) scannerMetricDeals.textContent = data.total_deals_notified || 0;

            if (scannerLastScan) {
                if (data.last_scan_time) {
                    const d = new Date(data.last_scan_time);
                    scannerLastScan.textContent = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                } else {
                    scannerLastScan.textContent = "Nunca";
                }
            }

            if (scannerNextScan) {
                if (data.is_running && data.next_scan_time) {
                    const d = new Date(data.next_scan_time);
                    scannerNextScan.textContent = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                } else {
                    scannerNextScan.textContent = data.is_running ? "Calculando..." : "En pausa";
                }
            }

            // 4. Formulario de Reglas (solo si no está siendo editado activamente)
            if (document.activeElement !== cfgKeywords) {
                if (cfgInterval) cfgInterval.value = data.interval_minutes || 20;
                if (cfgMinScore) cfgMinScore.value = data.min_score || 8.0;
                if (cfgMinSavings) cfgMinSavings.value = data.min_savings || 40;
                if (cfgKeywords && data.keywords) {
                    cfgKeywords.value = data.keywords.join(", ");
                }
            }

            // 5. Historial de Ciclos
            renderScannerHistory(data.scan_history || []);

        } catch (err) {
            console.error("Error al cargar estado del scanner:", err);
        }
    }

    function renderScannerHistory(history) {
        if (!scannerHistoryBody) return;
        if (!history || history.length === 0) {
            scannerHistoryBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">
                        Aún no se han completado ciclos de escaneo. Pulsa "⚡ Escanear Ahora" para lanzar el primero.
                    </td>
                </tr>
            `;
            if (scannerHistoryCount) scannerHistoryCount.textContent = "0 ciclos registrados";
            return;
        }

        if (scannerHistoryCount) scannerHistoryCount.textContent = `${history.length} ciclos recientes`;

        const rows = history.slice().reverse().map(c => {
            const dateStr = c.timestamp ? new Date(c.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : "N/A";
            const duration = c.duration_s ? `${c.duration_s}s` : "-";
            const listings = c.listings || 0;
            const deals = c.deals || 0;
            const alerts = c.alerts || 0;
            const badgeClass = deals > 0 ? "status-online" : "status-emulated";
            const badgeText = deals > 0 ? `🔥 ${deals} Chollos` : "Sin chollos";

            return `
                <tr>
                    <td><strong>${dateStr}</strong></td>
                    <td style="color: var(--text-muted);">${duration}</td>
                    <td>${listings}</td>
                    <td><span class="badge-status ${badgeClass}">${badgeText}</span></td>
                    <td><strong style="color: #10B981;">${alerts} enviadas</strong></td>
                    <td><span class="badge-status status-online">Completado</span></td>
                </tr>
            `;
        }).join("");

        scannerHistoryBody.innerHTML = rows;
    }

    // Botón Recargar Estado
    if (btnScannerRefresh) {
        btnScannerRefresh.addEventListener("click", () => {
            btnScannerRefresh.textContent = "⏳ Cargando...";
            loadScannerStatus().finally(() => {
                setTimeout(() => btnScannerRefresh.textContent = "🔄 Actualizar Estado", 800);
            });
        });
    }

    // Botón Probar Notificación Telegram
    if (btnTestTelegram) {
        btnTestTelegram.addEventListener("click", async () => {
            const token = sessionStorage.getItem("admin_token");
            if (!token) return;

            btnTestTelegram.disabled = true;
            btnTestTelegram.textContent = "📨 Enviando a Telegram...";
            if (tgTestFeedback) {
                tgTestFeedback.style.display = "none";
            }

            try {
                const res = await fetch("/api/admin/scanner/test-telegram", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    }
                });

                const data = await res.json();

                if (tgTestFeedback) {
                    tgTestFeedback.style.display = "block";
                    if (res.ok) {
                        tgTestFeedback.style.background = "rgba(16, 185, 129, 0.15)";
                        tgTestFeedback.style.color = "#34D399";
                        tgTestFeedback.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                        tgTestFeedback.textContent = data.message || "✅ ¡Mensaje recibido en Telegram!";
                    } else {
                        tgTestFeedback.style.background = "rgba(239, 68, 68, 0.15)";
                        tgTestFeedback.style.color = "#F87171";
                        tgTestFeedback.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                        tgTestFeedback.textContent = data.detail || "❌ Error al enviar mensaje.";
                    }
                }
            } catch (err) {
                if (tgTestFeedback) {
                    tgTestFeedback.style.display = "block";
                    tgTestFeedback.style.background = "rgba(239, 68, 68, 0.15)";
                    tgTestFeedback.style.color = "#F87171";
                    tgTestFeedback.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                    tgTestFeedback.textContent = "Error de conexión al probar Telegram.";
                }
            } finally {
                btnTestTelegram.disabled = false;
                btnTestTelegram.textContent = "🚀 Enviar Notificación de Prueba";
            }
        });
    }

    // Botón Toggle Iniciar/Pausar Scanner
    if (btnScannerToggle) {
        btnScannerToggle.addEventListener("click", async () => {
            const token = sessionStorage.getItem("admin_token");
            if (!token) return;

            const isStarting = btnScannerToggle.textContent.includes("Iniciar");
            const endpoint = isStarting ? "/api/admin/scanner/start" : "/api/admin/scanner/stop";

            btnScannerToggle.disabled = true;
            btnScannerToggle.textContent = "⏳ Procesando...";

            try {
                const res = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (res.ok) {
                    loadScannerStatus();
                } else {
                    alert("Error al cambiar estado del scanner.");
                }
            } catch (err) {
                alert("Error de conexión.");
            } finally {
                btnScannerToggle.disabled = false;
            }
        });
    }

    // Botón Escaneo Inmediato Manual
    if (btnScannerRunOnce) {
        btnScannerRunOnce.addEventListener("click", async () => {
            const token = sessionStorage.getItem("admin_token");
            if (!token) return;

            btnScannerRunOnce.disabled = true;
            btnScannerRunOnce.textContent = "⏳ Escaneando en background...";

            try {
                const res = await fetch("/api/admin/scanner/run-once", {
                    method: "POST",
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const data = await res.json();

                if (scannerActionFeedback) {
                    scannerActionFeedback.style.display = "block";
                    scannerActionFeedback.style.background = "rgba(59, 130, 246, 0.15)";
                    scannerActionFeedback.style.color = "#60A5FA";
                    scannerActionFeedback.style.border = "1px solid rgba(59, 130, 246, 0.3)";
                    scannerActionFeedback.textContent = "⚡ Ciclo lanzado. Si hay chollos te llegarán por Telegram. Recargando estado...";
                }

                // Poll de estado tras 5 y 15 segundos
                setTimeout(loadScannerStatus, 4000);
                setTimeout(loadScannerStatus, 12000);

            } catch (err) {
                alert("Error al lanzar escaneo.");
            } finally {
                setTimeout(() => {
                    btnScannerRunOnce.disabled = false;
                    btnScannerRunOnce.textContent = "⚡ Escanear Ahora";
                }, 3000);
            }
        });
    }

    // Formulario de Configuración del Scanner
    if (scannerConfigForm) {
        scannerConfigForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const token = sessionStorage.getItem("admin_token");
            if (!token) return;

            const kwList = cfgKeywords.value.split(",").map(s => s.strip ? s.strip() : s.trim()).filter(Boolean);

            const payload = {
                interval_minutes: parseInt(cfgInterval.value, 10),
                min_score: parseFloat(cfgMinScore.value),
                min_savings: parseFloat(cfgMinSavings.value),
                keywords: kwList
            };

            const btnSave = scannerConfigForm.querySelector("button[type='submit']");
            if (btnSave) {
                btnSave.disabled = true;
                btnSave.textContent = "💾 Guardando...";
            }

            try {
                const res = await fetch("/api/admin/scanner/config", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    if (cfgFeedback) {
                        cfgFeedback.style.display = "block";
                        cfgFeedback.style.background = "rgba(16, 185, 129, 0.15)";
                        cfgFeedback.style.color = "#34D399";
                        cfgFeedback.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                        cfgFeedback.textContent = "✅ Reglas y productos actualizados correctamente en tiempo real.";
                        setTimeout(() => cfgFeedback.style.display = "none", 4000);
                    }
                    loadScannerStatus();
                } else {
                    alert("No se pudo guardar la configuración.");
                }
            } catch (err) {
                alert("Error de conexión.");
            } finally {
                if (btnSave) {
                    btnSave.disabled = false;
                    btnSave.textContent = "💾 Guardar y Aplicar Reglas";
                }
            }
        });
    }
});

