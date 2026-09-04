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

    // Estado en memoria
    let rawScans = [];
    let filteredScans = [];

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
                applyFilters();
            }
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
});
