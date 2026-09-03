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
    const filterVerdict = document.getElementById("filter-verdict");
    const filterSort = document.getElementById("filter-sort");
    const btnRefresh = document.getElementById("btn-refresh");
    const btnExportCsv = document.getElementById("btn-export-csv");

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
            }

            // Cargar listado completo de productos
            const dataRes = await fetch("/api/admin/data?limit=200", {
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
        const verdict = filterVerdict.value;
        const sort = filterSort.value;

        // Filtrado
        filteredScans = rawScans.filter(item => {
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

    // 6. Renderizar tabla en pantalla
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
            const riskClass = (item.risk_level || "BAJO").toLowerCase();

            tr.innerHTML = `
                <td>
                    <span class="score-pill" style="background: ${scoreBg}; color: ${scoreColor};">
                        ★ ${score}
                    </span>
                </td>
                <td class="item-title-cell">
                    <a href="${item.url || '#'}" target="_blank" class="item-title-link" title="${item.title}">
                        ${item.title}
                    </a>
                    <span class="item-subtext">📦 ${item.normalized_product || 'General'} · ${item.platform.toUpperCase()}</span>
                </td>
                <td>
                    <div class="price-current">${item.price.toFixed(0)} €</div>
                </td>
                <td>
                    <div class="price-bench">${item.market_price ? item.market_price.toFixed(0) + ' €' : '-'}</div>
                </td>
                <td>${savingsHtml}</td>
                <td>
                    <div style="font-weight: 600;">⭐ ${item.seller_rating || 5.0}</div>
                    <div class="item-subtext">${item.seller_reviews || 0} reviews</div>
                </td>
                <td>
                    <span style="font-size: 0.8rem;">${item.has_shipping ? '✅ Disponible' : '🚫 En mano'}</span>
                </td>
                <td>
                    <span class="risk-badge risk-${riskClass}">${item.risk_level || 'NORMAL'}</span>
                </td>
                <td>
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-external">
                        ↗ Ver Anuncio
                    </a>
                </td>
            `;

            tableBody.appendChild(tr);
        });
    }

    // 7. Eventos de los filtros
    searchInput.addEventListener("input", applyFilters);
    filterVerdict.addEventListener("change", applyFilters);
    filterSort.addEventListener("change", applyFilters);
    btnRefresh.addEventListener("click", loadDashboard);

    // 8. Exportar a archivo CSV descargable
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
});
