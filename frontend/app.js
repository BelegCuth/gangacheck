document.addEventListener("DOMContentLoaded", () => {
    const scanForm = document.getElementById("scan-form");
    const urlInput = document.getElementById("url-input");
    const pasteBtn = document.getElementById("paste-btn");
    const submitBtn = document.getElementById("submit-btn");
    const loadingCard = document.getElementById("loading-card");
    const resultSection = document.getElementById("result-section");
    const demoChips = document.querySelectorAll(".demo-chip");
    const recentScansGrid = document.getElementById("recent-scans-grid");

    // Tacómetro SVG Elements
    const gaugeArc = document.getElementById("gauge-arc");
    const scoreNumber = document.getElementById("res-score-number");
    const verdictBadge = document.getElementById("res-verdict-badge");

    // Arc circumference constants
    const GAUGE_CIRCUMFERENCE = 251.2;

    // 1. Botón Pegar desde portapapeles
    if (pasteBtn && navigator.clipboard) {
        pasteBtn.addEventListener("click", async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text.trim();
                    urlInput.focus();
                }
            } catch (err) {
                console.log("Acceso a portapapeles no permitido");
            }
        });
    }

    // 2. Chips de demostración rápida
    demoChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const demoUrl = chip.getAttribute("data-url");
            urlInput.value = demoUrl;
            runScan(demoUrl);
        });
    });

    // 3. Envío del formulario
    scanForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (url) {
            runScan(url);
        }
    });

    // Función principal de escaneo
    async function runScan(url) {
        // UI State: Cargando
        loadingCard.classList.remove("hidden");
        resultSection.classList.add("hidden");
        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-text").textContent = "Escaneando...";

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                throw new Error("Error en la respuesta del servidor");
            }

            const data = await response.json();
            renderResults(data);
            loadRecentScans();

        } catch (error) {
            console.error("Error al analizar:", error);
            alert("Hubo un problema al analizar el enlace. Por favor verifica que la URL sea válida o prueba con uno de los ejemplos preconfigurados.");
        } finally {
            loadingCard.classList.add("hidden");
            submitBtn.disabled = false;
            submitBtn.querySelector(".btn-text").textContent = "Escanear";
        }
    }

    // Renderizar resultados en pantalla
    function renderResults(data) {
        const item = data.item;
        const ev = data.evaluation;
        const seller = item.seller || {};

        // Meta del producto
        document.getElementById("res-category").textContent = ev.category || "Segunda Mano";
        document.getElementById("res-title").textContent = item.title;
        document.getElementById("res-seller-name").textContent = seller.name || "Vendedor";
        document.getElementById("res-seller-stars").textContent = `⭐ ${seller.rating || 4.5}`;
        document.getElementById("res-seller-reviews").textContent = seller.reviews_count || 0;
        document.getElementById("res-shipping-status").textContent = item.shipping_available ? "📦 Envíos activos" : "🚫 Solo en mano";

        // Precios
        document.getElementById("res-item-price").textContent = `${ev.item_price.toFixed(2)} €`;
        document.getElementById("res-market-price").textContent = `${ev.market_price.toFixed(2)} €`;

        const savingsEl = document.getElementById("res-savings");
        if (ev.savings > 0) {
            savingsEl.textContent = `Ahorras ${ev.savings.toFixed(2)} € (-${Math.round(ev.savings_pct)}%)`;
            savingsEl.className = "metric-value price-savings";
        } else {
            savingsEl.textContent = `+${Math.abs(ev.savings).toFixed(2)} € (+${Math.abs(Math.round(ev.savings_pct))}%)`;
            savingsEl.style.color = "#EF4444";
        }

        // Animar Tacómetro
        animateGauge(ev.score);

        // Veredicto
        verdictBadge.textContent = ev.verdict;
        applyVerdictStyle(verdictBadge, ev.score, ev.risk_level);

        // Banderas Rojas
        const riskBox = document.getElementById("risk-alert-box");
        const riskList = document.getElementById("risk-list");
        riskList.innerHTML = "";
        if (ev.risk_flags && ev.risk_flags.length > 0) {
            riskBox.classList.remove("hidden");
            ev.risk_flags.forEach(flag => {
                const li = document.createElement("li");
                li.textContent = flag;
                riskList.appendChild(li);
            });
        } else {
            riskBox.classList.add("hidden");
        }

        // Pros
        const prosList = document.getElementById("res-pros-list");
        prosList.innerHTML = "";
        if (ev.pros && ev.pros.length > 0) {
            ev.pros.forEach(p => {
                const li = document.createElement("li");
                li.textContent = p;
                prosList.appendChild(li);
            });
        } else {
            prosList.innerHTML = "<li>Precio dentro del rango estándar.</li>";
        }

        // Contras
        const consList = document.getElementById("res-cons-list");
        consList.innerHTML = "";
        if (ev.cons && ev.cons.length > 0) {
            ev.cons.forEach(c => {
                const li = document.createElement("li");
                li.textContent = c;
                consList.appendChild(li);
            });
        } else {
            consList.innerHTML = "<li>No se han detectado inconvenientes reseñables.</li>";
        }

        // Afiliación
        const affBox = document.getElementById("affiliate-box");
        if (ev.affiliate) {
            affBox.classList.remove("hidden");
            document.getElementById("affiliate-title").textContent = ev.affiliate.title;
            document.getElementById("affiliate-desc").textContent = ev.affiliate.description;
            document.getElementById("affiliate-btn").textContent = ev.affiliate.button_text;
        } else {
            affBox.classList.add("hidden");
        }

        // Mostrar sección con scroll suave
        resultSection.classList.remove("hidden");
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // Animación suave del tacómetro
    function animateGauge(finalScore) {
        const offset = GAUGE_CIRCUMFERENCE - (finalScore / 10) * GAUGE_CIRCUMFERENCE;
        gaugeArc.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.2, 0.8, 0.2, 1)";
        gaugeArc.style.strokeDashoffset = offset;

        // Conteo del número
        let current = 0.0;
        const step = finalScore / 40;
        const interval = setInterval(() => {
            current += step;
            if (current >= finalScore) {
                current = finalScore;
                clearInterval(interval);
            }
            scoreNumber.textContent = current.toFixed(1);
        }, 25);
    }

    function applyVerdictStyle(el, score, riskLevel) {
        if (riskLevel === "ALTO" || score < 3.5) {
            el.style.background = "rgba(239, 68, 68, 0.15)";
            el.style.color = "#F87171";
            el.style.borderColor = "rgba(239, 68, 68, 0.3)";
        } else if (score < 7.2) {
            el.style.background = "rgba(245, 158, 11, 0.15)";
            el.style.color = "#FBBF24";
            el.style.borderColor = "rgba(245, 158, 11, 0.3)";
        } else {
            el.style.background = "rgba(16, 185, 129, 0.15)";
            el.style.color = "#34D399";
            el.style.borderColor = "rgba(16, 185, 129, 0.3)";
        }
    }

    // Cargar historial de análisis recientes
    async function loadRecentScans() {
        try {
            const res = await fetch("/api/history?limit=6");
            const data = await res.json();
            const scans = data.scans || [];

            recentScansGrid.innerHTML = "";
            if (scans.length === 0) {
                recentScansGrid.innerHTML = "<p style='color: var(--text-muted); font-size: 0.85rem;'>Aún no hay análisis recientes. ¡Sé el primero en probar!</p>";
                return;
            }

            scans.forEach(s => {
                const card = document.createElement("div");
                card.className = "recent-card";

                let badgeClass = "badge-green";
                if (s.score < 3.5) badgeClass = "badge-red";
                else if (s.score < 7.2) badgeClass = "badge-yellow";

                card.innerHTML = `
                    <div class="recent-info">
                        <h5 title="${s.title}">${s.title}</h5>
                        <div class="recent-price">${s.price.toFixed(0)} € (Habitual: ${s.market_price ? s.market_price.toFixed(0) + ' €' : '-'})</div>
                    </div>
                    <div class="recent-badge ${badgeClass}">${s.score.toFixed(1)} / 10</div>
                `;
                recentScansGrid.appendChild(card);
            });
        } catch (e) {
            console.log("No se pudo cargar el historial", e);
        }
    }

    // Cargar al inicio
    loadRecentScans();
});
