// Cache-busting version — bump this whenever the CSVs, CSS, or JS change, so
// browsers stop serving stale files (the cause of the VE / Execution column-shift).
const SITE_VERSION = "20261026b";

// Table registry: which CSV feeds which table, and how values are rendered.
//   percent — values in [0,1] are shown as % with a progress bar (execution / objective / multilingual)
//   raw     — values are raw scores, shown as-is with a heat-map background (VE metrics)
const TABLE_CONFIG = [
    { csv: "execution.csv",    id: "execution-table",     mode: "percent", pass5Note: true },
    { csv: "objective.csv",    id: "objective-table",     mode: "percent", pass5Note: true },
    { csv: "ve.csv",           id: "ve-table",            mode: "percent" },
    { csv: "multilang-exe.csv", id: "multilang-exe-table", mode: "percent" },
    { csv: "multilang-obj.csv", id: "multilang-obj-table", mode: "percent" },
];

// Non-result (categorical) columns get a static filter dropdown.
const NON_RESULT_COLS = new Set([
    "Model", "Modality", "Source", "Output Format", "Language", "Scope", "Report By", "Report Date",
]);

// Green (high) → red (low) on the HSL wheel.
function getColorByPercent(pct) {
    const h = Math.max(0, Math.min(1, pct)) * 120;
    return `hsl(${h}, 80%, 46%)`;
}

// Compact number formatting: keep integers whole, otherwise up to 2 decimals.
function fmtNum(num) {
    if (Number.isInteger(num)) return String(num);
    return num.toFixed(2).replace(/\.?0+$/, "");
}

function isEmpty(val) {
    return val === "" || val === "-" || val === "None" || val == null;
}

// Logo family mapping: model name -> icon file in Logo/.
function logoForModel(name) {
    const n = String(name).toLowerCase();
    if (n.includes("gemini")) return "gemini.svg";
    if (n.includes("deepseek")) return "deepseek.png";
    if (n.includes("gpt") || n.includes("openhands")) return "gpt.svg";
    if (n.includes("gemma") || n.includes("codegemma")) return "gemma.png";
    if (n.includes("voxtral") || n.includes("mistral") || n.includes("ministral")) return "mistral.svg";
    if (n.includes("qwen")) return "qwen.svg";
    if (n.includes("llama") || n.includes("codellama")) return "llama.svg";
    if (n.includes("phi")) return "phi.svg";
    return null; // e.g. StarCoder2-7B — no logo available
}

function logoForLang(lang) {
    const l = String(lang).toLowerCase();
    if (l === "py" || l === "python") return "python.png";
    if (l === "ja" || l === "java") return "java.png";
    if (l === "js" || l === "javascript") return "javascript.svg";
    return null;
}

function prependLogo(td, file, cls) {
    const img = document.createElement("img");
    img.src = "Logo/" + file;
    img.alt = "";
    img.className = cls;
    img.loading = "lazy";
    td.prepend(img);
}

// UTF-8 icons for the Modality column values.
function modalityIcon(val) {
    const v = String(val).toLowerCase();
    if (v === "text") return "📝 ";
    if (v === "audio") return "🔊 ";
    if (v === "vision") return "👁️ ";
    return "";
}

// Model family (used for same-color row tinting): derived from the logo family.
function familyForModel(name) {
    const logo = logoForModel(name);
    return logo ? logo.split(".")[0] : null;
}

// Version-based darkness within a logo family: higher version → darker shade (0 = lightest).
const FAMILY_VERSION_RANGE = {
    gemini: [1.5, 3.8],
    gpt: [0, 6],
    gemma: [0, 4],
    mistral: [0, 3],
    qwen: [2.5, 3.8],
    llama: [0, 3.3],
    phi: [3, 4],
    deepseek: [0, 4],
};

function versionRank(name) {
    const n = String(name).toLowerCase();
    // Model lines whose first number is a parameter size, not a version.
    if (n.includes("codellama") || n.includes("deepseek-coder") ||
        n.includes("gpt-oss") || n.includes("voxtral") || n.includes("codegemma")) {
        return 0;
    }
    // Bare "Gemma-7B" (only a size) and "Mistral-7B-v0.x" (size, no generation).
    if (/^gemma-?\d+b/.test(n)) return 1;   // Gemma-7B → original Gemma (v1)
    if (/^mistral-?\d+b/.test(n)) return 0; // Mistral-7B-v0.3 → base Mistral
    const m = n.match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
}

function shadeForModel(name) {
    const family = familyForModel(name);
    const range = family && FAMILY_VERSION_RANGE[family];
    if (!range || range[1] <= range[0]) return 0;
    const shade = (versionRank(name) - range[0]) / (range[1] - range[0]);
    return Math.max(0, Math.min(1, shade));
}

// Themed hues for categorical tag pills; unknown values (e.g. Report Date) stay neutral.
const TAG_HUE = {
    "api": 217,
    "open-source": 152,
    "text": 205,
    "audio": 262,
    "vision": 326,
    "point": 24,
    "project": 250,
    "json": 210,
    "py": 210,
    "ja": 24,
    "js": 45,
    "projecteval": 230,
    "projectevalm": 262,
    "projectevalplus": 170,
};

function tagHue(value) {
    const key = String(value).trim().toLowerCase();
    return (key in TAG_HUE) ? TAG_HUE[key] : null;
}

function renderPercentCell(td, raw) {
    const val = raw == null ? "" : String(raw).trim();
    if (isEmpty(val)) {
        td.textContent = "-";
        td.classList.add("dim");
        return;
    }
    const num = parseFloat(val);
    if (isNaN(num)) {
        td.textContent = val;
        return;
    }
    if (num >= 0 && num <= 1) {
        const pct = num * 100;
        td.textContent = pct.toFixed(2) + "%";
        td.setAttribute("data-progress", "");
        td.style.setProperty("--progress-color", getColorByPercent(num));
        td.style.setProperty("--progress-width", pct.toFixed(2) + "%");
    } else {
        td.textContent = val;
    }
}

function renderRawCell(td, raw) {
    const val = raw == null ? "" : String(raw).trim();
    if (isEmpty(val)) {
        td.textContent = "-";
        td.classList.add("dim");
        return;
    }
    const num = parseFloat(val);
    if (isNaN(num)) {
        td.textContent = val;
        return;
    }
    td.textContent = fmtNum(num);
    td.setAttribute("data-heat", "");
}

function loadTable(cfg) {
    const table = document.getElementById(cfg.id);
    const tbody = table.querySelector("tbody");

    return fetch(cfg.csv + "?v=" + SITE_VERSION)
        .then((r) => r.text())
        .then((csv) => {
            const parsed = Papa.parse(csv, { header: true, skipEmptyLines: true });
            const cols = parsed.meta.fields;
            const frag = document.createDocumentFragment();

            parsed.data.forEach((row) => {
                const tr = document.createElement("tr");
                tr._row = row; // keep raw values for static filtering
                const family = familyForModel(row["Model"]);
                if (family) {
                    tr.classList.add("family-" + family);
                    tr.style.setProperty("--fam-shade", shadeForModel(row["Model"]).toFixed(2));
                }
                cols.forEach((col) => {
                    const td = document.createElement("td");
                    if (cfg.mode === "percent") {
                        renderPercentCell(td, row[col]);
                    } else {
                        renderRawCell(td, row[col]);
                    }
                    // Original ProjectEval rows are Pass@5 — mark them with a dagger.
                    if (cfg.pass5Note && col === "Report By" && String(row[col]).trim() === "ProjectEval") {
                        const sup = document.createElement("sup");
                        sup.textContent = "†";
                        sup.title = "Pass@5";
                        td.appendChild(document.createTextNode(" "));
                        td.appendChild(sup);
                    }
                    // Add model / language icons and modality icons before the text.
                    if (col === "Model") {
                        const logo = logoForModel(row[col]);
                        if (logo) prependLogo(td, logo, "model-logo");
                    } else if (col === "Language") {
                        const logo = logoForLang(row[col]);
                        if (logo) prependLogo(td, logo, "lang-logo");
                    } else if (col === "Modality") {
                        td.prepend(document.createTextNode(modalityIcon(row[col])));
                    } else if (col === "Report By") {
                        const rb = String(row[col] || "").trim();
                        if (rb.startsWith("ProjectEval")) {
                            // Distinguishing mark first (so the logo ends up in front after the next prepend).
                            if (rb === "ProjectEval") {
                                const ck = document.createElement("span");
                                ck.className = "rb-badge rb-check";
                                ck.textContent = "✓";
                                td.prepend(ck);
                            } else if (rb === "ProjectEvalM") {
                                const b = document.createElement("span");
                                b.className = "rb-badge rb-m";
                                b.textContent = "M";
                                td.prepend(b);
                            } else if (rb === "ProjectEvalPlus") {
                                const b = document.createElement("span");
                                b.className = "rb-badge rb-p";
                                b.textContent = "P";
                                td.prepend(b);
                            }
                            const img = document.createElement("img");
                            img.src = "Logo/projecteval.svg";
                            img.alt = "";
                            img.className = "rb-logo";
                            td.prepend(img);
                        }
                    }
                    // Wrap categorical (non-result) columns in a small pill tag.
                    if (col !== "Model" && NON_RESULT_COLS.has(col)) {
                        const tag = document.createElement("span");
                        tag.className = "tag";
                        const hue = tagHue(row[col]);
                        if (hue != null) {
                            tag.classList.add("tag-colored");
                            tag.style.setProperty("--tag-hue", hue);
                        }
                        while (td.firstChild) tag.appendChild(td.firstChild);
                        td.appendChild(tag);
                    }
                    tr.appendChild(td);
                });
                frag.appendChild(tr);
            });

            tbody.appendChild(frag);

            applyDefaultSort(cfg.id);

            if (cfg.mode === "raw") {
                applyHeatMap(tbody);
            }

            buildFilters(table, cols, parsed.data);
            chartData[cfg.id] = { cols, data: parsed.data };
        });
}

// For raw-mode tables, colour each numeric cell by its magnitude relative to
// the column maximum (green = highest, red = lowest).
function applyHeatMap(tbody) {
    const rows = Array.from(tbody.querySelectorAll("tr"));
    if (rows.length === 0) return;

    const colCount = rows[0].querySelectorAll("td").length;
    const maxes = new Array(colCount).fill(0);

    rows.forEach((tr) => {
        const tds = tr.querySelectorAll("td");
        for (let i = 0; i < tds.length; i++) {
            const td = tds[i];
            if (!td.hasAttribute("data-heat")) continue;
            const v = parseFloat(td.textContent);
            if (!isNaN(v) && v > maxes[i]) maxes[i] = v;
        }
    });

    rows.forEach((tr) => {
        const tds = tr.querySelectorAll("td");
        for (let i = 0; i < tds.length; i++) {
            const td = tds[i];
            if (!td.hasAttribute("data-heat")) continue;
            const v = parseFloat(td.textContent);
            if (isNaN(v) || maxes[i] === 0) continue;
            const norm = v / maxes[i];
            td.style.setProperty("--heat-color", getColorByPercent(norm));
            td.style.setProperty("--heat-width", (norm * 100).toFixed(1) + "%");
        }
    });
}

// ---------- Static filtering (non-result columns) ----------

function buildFilters(table, cols, data) {
    const nonResult = cols.filter((c) => NON_RESULT_COLS.has(c));
    if (nonResult.length === 0) return;

    const bar = document.createElement("div");
    bar.className = "filters";

    nonResult.forEach((col) => {
        const values = [...new Set(
            data.map((r) => String(r[col] == null ? "" : r[col]).trim()).filter(Boolean)
        )].sort();
        const select = document.createElement("select");
        select.dataset.col = col;
        select.setAttribute("aria-label", col);
        const all = document.createElement("option");
        all.value = "";
        all.textContent = col + ": All";
        select.appendChild(all);
        values.forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v;
            opt.textContent = v;
            select.appendChild(opt);
        });
        select.addEventListener("change", () => applyFilters(table));
        bar.appendChild(select);
    });

    table.parentElement.insertBefore(bar, table);
}

function applyFilters(table) {
    const selects = Array.from(table.parentElement.querySelectorAll(".filters select"));
    const tbody = table.querySelector("tbody");
    tbody.querySelectorAll("tr").forEach((tr) => {
        const row = tr._row || {};
        let show = true;
        selects.forEach((sel) => {
            if (show && sel.value !== "") {
                const raw = String(row[sel.dataset.col] == null ? "" : row[sel.dataset.col]).trim();
                if (raw !== sel.value) show = false;
            }
        });
        tr.style.display = show ? "" : "none";
    });
}

// ---------- Sorting ----------

// Resolve a header cell to its real column index, accounting for the
// rowspan/colspan structure of the multi-row thead.
function getRealColumnIndex(th) {
    const table = th.closest("table");
    const headerRows = Array.from(table.querySelectorAll("thead tr"));
    const targetRowIndex = headerRows.indexOf(th.parentElement);
    const matrix = [];

    headerRows.forEach((tr, rowIdx) => {
        if (!matrix[rowIdx]) matrix[rowIdx] = [];
        let colCursor = 0;
        tr.querySelectorAll("th").forEach((cell) => {
            while (matrix[rowIdx][colCursor]) colCursor++;
            const rowspan = parseInt(cell.getAttribute("rowspan")) || 1;
            const colspan = parseInt(cell.getAttribute("colspan")) || 1;
            for (let r = 0; r < rowspan; r++) {
                if (!matrix[rowIdx + r]) matrix[rowIdx + r] = [];
                for (let c = 0; c < colspan; c++) {
                    matrix[rowIdx + r][colCursor + c] = cell;
                }
            }
            colCursor += colspan;
        });
    });

    for (let c = 0; c < matrix[targetRowIndex].length; c++) {
        if (matrix[targetRowIndex][c] === th) return c;
    }
    return -1;
}

function getSortValue(tr, col) {
    const td = tr.querySelectorAll("td")[col];
    if (!td) return "";
    const text = td.textContent.trim();
    const num = parseFloat(text.replace(/%/g, "").replace(/,/g, ""));
    if (!isNaN(num)) return num;
    return text.toLowerCase();
}

function sortTable(table, th) {
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));
    const col = getRealColumnIndex(th);
    if (col < 0) return;

    const asc = !th.classList.contains("asc");
    table.querySelectorAll("th.sortable").forEach((h) => h.classList.remove("asc", "desc"));
    th.classList.add(asc ? "asc" : "desc");

    rows.sort((a, b) => {
        const av = getSortValue(a, col);
        const bv = getSortValue(b, col);
        let cmp;
        if (typeof av === "number" && typeof bv === "number") {
            cmp = av - bv;
        } else {
            cmp = String(av).localeCompare(String(bv));
        }
        return asc ? cmp : -cmp;
    });

    rows.forEach((r) => tbody.appendChild(r));
}

function initializeSorting() {
    TABLE_CONFIG.forEach((cfg) => {
        const table = document.getElementById(cfg.id);
        table.querySelectorAll("th.sortable").forEach((th) => {
            th.addEventListener("click", () => sortTable(table, th));
        });
    });
}

// ---------- Default sort on load ----------
// Sort keys are CSV column names (each table's tbody cell order matches the CSV
// field order), so we can read precise values straight from tr._row.
const LANG_ORDER = { py: 0, ja: 1, js: 2 };

const DEFAULT_SORT = {
    "execution-table":     [["All-Avg", "desc"]],
    "objective-table":     [["Direct-Level1-Code", "desc"]],
    "ve-table":            [["Scope", "asc"], ["Function-Avg", "desc"]],
    "multilang-exe-table": [["Direct-Level1-py", "desc"]],
    "multilang-obj-table": [["Language", "asc"], ["Direct-Level1-Code", "desc"]],
};

function sortKeyFor(row, col) {
    const raw = row[col];
    if (raw == null) return null;
    const s = String(raw).trim();
    if (s === "" || s === "-" || s === "None" || s === "none") return null;
    if (col === "Language") {
        const k = LANG_ORDER[s.toLowerCase()];
        return k != null ? k : 99;
    }
    const num = parseFloat(s);
    return isNaN(num) ? s.toLowerCase() : num;
}

function applyDefaultSort(tableId) {
    const spec = DEFAULT_SORT[tableId];
    if (!spec || spec.length === 0) return;
    const table = document.getElementById(tableId);
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort((a, b) => {
        for (const [col, dir] of spec) {
            const av = sortKeyFor(a._row, col);
            const bv = sortKeyFor(b._row, col);
            let cmp = 0;
            if (av === null && bv === null) cmp = 0;
            else if (av === null) cmp = 1;   // missing ("-") sinks to the bottom
            else if (bv === null) cmp = -1;
            else if (typeof av === "number" && typeof bv === "number") cmp = av - bv;
            else cmp = String(av).localeCompare(String(bv));
            if (cmp !== 0) return dir === "desc" ? -cmp : cmp;
        }
        return 0;
    });

    rows.forEach((r) => tbody.appendChild(r));
}

// ---------- Bar chart (single, dataset + metric selectable) ----------
// Each loaded dataset's raw rows and columns are stashed here by loadTable(),
// then one combined chart is built once every table has finished loading.
const chartData = {}; // tableId -> { cols, data }

const CHART_DATASETS = {
    "execution-table":     { label: "Execution (Pass@1)",       defaultMetric: "All-Avg" },
    "objective-table":     { label: "Objective Metrics",         defaultMetric: "Direct-Level1-Code" },
    "ve-table":            { label: "Visual Evaluation",         defaultMetric: "Function-Avg" },
    "multilang-exe-table": { label: "Multi-language Execution",  defaultMetric: "Direct-Level1-py" },
    "multilang-obj-table": { label: "Multi-language Objective",  defaultMetric: "Direct-Level1-Code" },
};

// One bar per data row; prepend the modality icon and append Scope / Language so
// each (model, modality, scope, language) combination gets a unique label.
function chartLabel(row) {
    let lbl = "";
    const mod = row["Modality"];
    if (mod != null && String(mod).trim()) lbl += modalityIcon(mod);
    lbl += String(row["Model"] == null ? "" : row["Model"]).trim();
    const scope = String(row["Scope"] == null ? "" : row["Scope"]).trim();
    if (scope) lbl += " · " + scope;
    const lang = String(row["Language"] == null ? "" : row["Language"]).trim();
    if (lang) lbl += " · " + lang;
    return lbl;
}

const chartRegistry = {}; // tableId -> render()

function chartThemeColors() {
    const cs = getComputedStyle(document.documentElement);
    return {
        text: cs.getPropertyValue("--text-dim").trim() || "#5b6474",
        grid: cs.getPropertyValue("--border").trim() || "#e3e8f0",
    };
}

function buildChart() {
    if (typeof Chart === "undefined") return; // Chart.js CDN unavailable — skip chart
    const card = document.getElementById("chart-card");
    if (!card) return;
    const datasetSelect = card.querySelector(".chart-dataset");
    const metricSelect = card.querySelector(".chart-metric");
    const wrap = card.querySelector(".chart-wrap");
    const canvas = card.querySelector("canvas");
    if (!datasetSelect || !metricSelect || !wrap || !canvas) return;

    // Only offer datasets that actually loaded and expose numeric columns.
    const ids = TABLE_CONFIG
        .map((c) => c.id)
        .filter((id) => chartData[id] && chartData[id].cols.some((c) => !NON_RESULT_COLS.has(c)));

    datasetSelect.innerHTML = "";
    ids.forEach((id) => {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = CHART_DATASETS[id].label;
        datasetSelect.appendChild(opt);
    });
    if (ids.length === 0) return;
    datasetSelect.value = ids[0];

    function numericColsFor(id) {
        return chartData[id].cols.filter((c) => !NON_RESULT_COLS.has(c));
    }

    function populateMetrics(id) {
        const numericCols = numericColsFor(id);
        metricSelect.innerHTML = "";
        numericCols.forEach((c) => {
            const opt = document.createElement("option");
            opt.value = c;
            opt.textContent = c;
            if (c === CHART_DATASETS[id].defaultMetric) opt.selected = true;
            metricSelect.appendChild(opt);
        });
    }

    let chart = null;
    function render() {
        const id = datasetSelect.value;
        const meta = CHART_DATASETS[id];
        const numericCols = numericColsFor(id);
        if (!meta || numericCols.length === 0) return;
        const metric = metricSelect.value || numericCols[0];
        const data = chartData[id].data;
        const mobile = window.innerWidth < 768;
        const theme = chartThemeColors();

        const rows = data
            .map((r) => ({
                label: chartLabel(r),
                val: parseFloat(String(r[metric] == null ? "" : r[metric]).trim()),
            }))
            .filter((r) => !isNaN(r.val))
            .sort((a, b) => b.val - a.val);

        // Horizontal bars render the first item at the bottom, so reverse to put the best at the top.
        if (mobile) rows.reverse();

        const labels = rows.map((r) => r.label);
        const values = rows.map((r) => r.val);
        const colors = values.map((v) => getColorByPercent(v));

        wrap.style.height = mobile
            ? Math.max(rows.length * 24 + 34, 240) + "px"
            : "320px";

        const catAxis = mobile ? "y" : "x";
        const valAxis = mobile ? "x" : "y";

        if (chart) chart.destroy();
        chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: "rgba(0,0,0,0.10)",
                    borderWidth: 1,
                    borderRadius: mobile ? 4 : 2,
                    maxBarThickness: mobile ? 20 : 42,
                }],
            },
            options: {
                indexAxis: mobile ? "y" : "x",
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 220 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        displayColors: false,
                        callbacks: {
                            title: (items) => (items.length ? items[0].label : ""),
                            label: (ctx) => " " + (ctx.raw * 100).toFixed(2) + "%",
                        },
                    },
                },
                scales: {
                    [catAxis]: {
                        grid: { display: false },
                        ticks: {
                            autoSkip: !mobile,
                            maxRotation: 0,
                            color: theme.text,
                            font: { size: mobile ? 11 : 10 },
                        },
                    },
                    [valAxis]: {
                        beginAtZero: true,
                        grid: { color: theme.grid },
                        ticks: {
                            callback: (v) => Math.round(v * 100) + "%",
                            color: theme.text,
                            font: { size: 10 },
                        },
                    },
                },
            },
        });
    }

    datasetSelect.addEventListener("change", () => {
        populateMetrics(datasetSelect.value);
        render();
    });
    metricSelect.addEventListener("change", render);

    chartRegistry.main = { render };
    populateMetrics(datasetSelect.value);
    render();
}

// Re-render charts when crossing the mobile breakpoint or switching colour scheme.
let chartWasMobile = null;
window.addEventListener("resize", () => {
    const mobile = window.innerWidth < 768;
    if (mobile === chartWasMobile) return;
    chartWasMobile = mobile;
    Object.keys(chartRegistry).forEach((id) => chartRegistry[id].render());
});
if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        Object.keys(chartRegistry).forEach((id) => chartRegistry[id].render());
    });
}

// ---------- Boot ----------
Promise.all(TABLE_CONFIG.map(loadTable)).then(() => {
    initializeSorting();
    buildChart();
});
