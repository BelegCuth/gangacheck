document.addEventListener("DOMContentLoaded", () => {
    const scanForm = document.getElementById("scan-form");
    const urlInput = document.getElementById("url-input");
    const pasteBtn = document.getElementById("paste-btn");
    const submitBtn = document.getElementById("submit-btn");
    const loadingCard = document.getElementById("loading-card");
    const resultSection = document.getElementById("result-section");
    const demoChips = document.querySelectorAll(".demo-chip");
    const recentScansGrid = document.getElementById("recent-scans-grid");
    const btnShareResult = document.getElementById("btn-share-result");
    const toast = document.getElementById("toast");
    const historyChips = document.querySelectorAll(".history-chip");

    // Tacómetro SVG Elements
    const gaugeArc = document.getElementById("gauge-arc");
    const scoreNumber = document.getElementById("res-score-number");
    const verdictBadge = document.getElementById("res-verdict-badge");

    // Sub-scores Elements
    const subPriceVal = document.getElementById("sub-price-val");
    const subPriceBar = document.getElementById("sub-price-bar");
    const subSellerVal = document.getElementById("sub-seller-val");
    const subSellerBar = document.getElementById("sub-seller-bar");
    const subCondVal = document.getElementById("sub-cond-val");
    const subCondBar = document.getElementById("sub-cond-bar");

    const GAUGE_CIRCUMFERENCE = 251.2;
    let currentScan = null;
    let allRecentScans = [];

    // Helper Toast
    function showToast(msg) {
        if (!toast) return;
        toast.textContent = msg;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 2800);
    }

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
                console.log("Acceso a portapapeles restringido");
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
            currentScan = data;
            renderResults(data);
            loadRecentScans();

        } catch (error) {
            console.error("Error al analizar:", error);
            alert("Hubo un problema al analizar el enlace. Por favor verifica que la URL sea válida o prueba con los ejemplos preconfigurados.");
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

        // Meta del producto y plataforma
        const platform = (item.platform || "wallapop").toUpperCase();
        document.getElementById("res-category").textContent = `${platform} · ${ev.category || "Segunda Mano"}`;
        document.getElementById("res-title").textContent = item.title;
        document.getElementById("res-seller-name").textContent = seller.name || "Vendedor";
        document.getElementById("res-seller-stars").textContent = `⭐ ${seller.rating || 4.8}`;
        document.getElementById("res-seller-reviews").textContent = seller.reviews_count || 0;
        document.getElementById("res-shipping-status").textContent = item.shipping_available ? "📦 Envíos activos" : "🚫 Solo en mano";

        // Precios
        document.getElementById("res-item-price").textContent = `${ev.item_price.toFixed(0)} €`;
        document.getElementById("res-market-price").textContent = `${ev.market_price.toFixed(0)} €`;

        const savingsEl = document.getElementById("res-savings");
        if (ev.savings > 0) {
            savingsEl.textContent = `Ahorras ${ev.savings.toFixed(0)} € (-${Math.round(ev.savings_pct)}%)`;
            savingsEl.className = "metric-value price-savings";
        } else {
            savingsEl.textContent = `+${Math.abs(ev.savings).toFixed(0)} € (+${Math.abs(Math.round(ev.savings_pct))}%)`;
            savingsEl.style.color = "#EF4444";
        }

        // Animar Tacómetro
        animateGauge(ev.score);

        // Veredicto
        verdictBadge.textContent = ev.verdict;
        applyVerdictStyle(verdictBadge, ev.score, ev.risk_level);

        // Sub-scores Breakdown
        const subs = ev.subscores || { price: ev.score, seller: 8.0, condition: 8.0 };
        if (subPriceVal && subPriceBar) {
            subPriceVal.textContent = `${subs.price.toFixed(1)} / 10`;
            subSellerVal.textContent = `${subs.seller.toFixed(1)} / 10`;
            subCondVal.textContent = `${subs.condition.toFixed(1)} / 10`;

            // Animar anchuras de las barras
            setTimeout(() => {
                subPriceBar.style.width = `${Math.min(100, subs.price * 10)}%`;
                subSellerBar.style.width = `${Math.min(100, subs.seller * 10)}%`;
                subCondBar.style.width = `${Math.min(100, subs.condition * 10)}%`;
            }, 150);
        }

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
            prosList.innerHTML = "<li>Precio dentro del rango habitual de mercado.</li>";
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
            consList.innerHTML = "<li>No se han detectado señales negativas.</li>";
        }

        // Afiliación inteligente
        const affBox = document.getElementById("affiliate-box");
        if (ev.affiliate) {
            affBox.classList.remove("hidden");
            document.getElementById("affiliate-title").textContent = ev.affiliate.title;
            document.getElementById("affiliate-desc").textContent = ev.affiliate.description;
            document.getElementById("affiliate-btn").textContent = ev.affiliate.button_text;
        } else {
            affBox.classList.add("hidden");
        }

        // Scroll suave al resultado
        resultSection.classList.remove("hidden");
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // Botón Compartir / Copiar Análisis
    if (btnShareResult) {
        btnShareResult.addEventListener("click", async () => {
            if (!currentScan) return;
            const it = currentScan.item;
            const ev = currentScan.evaluation;

            const shareText = 
                `🔥 Análisis en GangaCheck.es:\n` +
                `📦 "${it.title}"\n` +
                `⭐ Nota: ${ev.score} / 10 (${ev.verdict})\n` +
                `💶 Precio: ${it.price.toFixed(0)} € (Mediana BBDD: ${ev.market_price.toFixed(0)} €)\n` +
                `👉 Tasa cualquier anuncio gratis en: https://gangacheck.onrender.com`;

            if (navigator.share) {
                try {
                    await navigator.share({
                        title: "GangaCheck.es - Tasador de Segunda Mano",
                        text: shareText,
                        url: "https://gangacheck.onrender.com"
                    });
                    return;
                } catch (err) {
                    // Si el usuario cancela, continuar al fallback
                }
            }

            if (navigator.clipboard) {
                await navigator.clipboard.writeText(shareText);
                showToast("¡Análisis copiado al portapapeles!");
            }
        });
    }

    // Animación suave del tacómetro
    function animateGauge(finalScore) {
        const offset = GAUGE_CIRCUMFERENCE - (finalScore / 10) * GAUGE_CIRCUMFERENCE;
        gaugeArc.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.2, 0.8, 0.2, 1)";
        gaugeArc.style.strokeDashoffset = offset;

        let current = 0.0;
        const step = finalScore / 35;
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

    // Cargar historial de la comunidad con filtros reactivos
    async function loadRecentScans() {
        try {
            const res = await fetch("/api/history?limit=12");
            const data = await res.json();
            allRecentScans = data.scans || [];
            renderHistoryCards("all");
        } catch (e) {
            console.log("No se pudo cargar el historial", e);
        }
    }

    function renderHistoryCards(filter) {
        recentScansGrid.innerHTML = "";

        const filtered = allRecentScans.filter(s => {
            if (filter === "all") return true;
            if (filter === "chollos") return parseFloat(s.score || 0) >= 7.5;
            if (filter === "wallapop") return (s.platform || "").toLowerCase() === "wallapop";
            if (filter === "vinted") return (s.platform || "").toLowerCase() === "vinted";
            if (filter === "milanuncios") return (s.platform || "").toLowerCase() === "milanuncios";
            return true;
        });

        if (filtered.length === 0) {
            recentScansGrid.innerHTML = "<p style='color: var(--text-muted); font-size: 0.85rem;'>No hay análisis en esta categoría todavía.</p>";
            return;
        }

        filtered.forEach(s => {
            const card = document.createElement("div");
            card.className = "recent-card";

            let badgeClass = "badge-green";
            if (s.score < 3.5) badgeClass = "badge-red";
            else if (s.score < 7.2) badgeClass = "badge-yellow";

            const platBadge = (s.platform || "wallapop").slice(0, 1).toUpperCase();

            card.innerHTML = `
                <div class="recent-info">
                    <h5 title="${s.title}">[${platBadge}] ${s.title}</h5>
                    <div class="recent-price">${s.price.toFixed(0)} € · Habitual: ${s.market_price ? s.market_price.toFixed(0) + ' €' : '-'}</div>
                </div>
                <div class="recent-badge ${badgeClass}">${s.score.toFixed(1)} / 10</div>
            `;
            recentScansGrid.appendChild(card);
        });
    }

    // Filtros del historial
    historyChips.forEach(chip => {
        chip.addEventListener("click", () => {
            historyChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            const f = chip.getAttribute("data-filter");
            renderHistoryCards(f);
        });
    });

    // Cargar al inicio
    loadRecentScans();
});
