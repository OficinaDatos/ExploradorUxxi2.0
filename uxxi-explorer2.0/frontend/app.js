let API = "";

const $ = (id) => document.getElementById(id);

function setStatus(msg) { $("status").textContent = msg; }
function setOut(obj) { $("output").textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2); }
function clearErr() { $("errOwners").textContent = ""; $("errTables").textContent = ""; $("errOutput").textContent = ""; }

async function apiGet(path) {
    const res = await fetch(`${API}${path}`);
    const txt = await res.text();
    let json = null;
    try { json = JSON.parse(txt); } catch { }
    if (!res.ok) throw new Error((json && json.detail) ? json.detail : txt);
    return json ?? txt;
}

async function loadOwners() {
    clearErr();
    try {
        const data = await apiGet(`/meta/owners`);
        const sel = $("owners");
        sel.innerHTML = "";

        // ✅ El backend devuelve "propietarios"
        const owners = data.propietarios || [];

        owners.forEach(o => {
            const opt = document.createElement("option");
            opt.value = o; opt.textContent = o;
            sel.appendChild(opt);
        });

        setStatus(`Owners cargados: ${owners.length}`);
    } catch (e) {
        $("errOwners").textContent = e.message;
    }
}

async function loadTables() {
    clearErr();
    const owner = $("owners").value;
    try {
        const data = await apiGet(`/meta/tables?owner=${encodeURIComponent(owner)}`);
        const sel = $("tables");
        sel.innerHTML = "";
        (data.tables || []).forEach(t => {
            const opt = document.createElement("option");
            opt.value = t; opt.textContent = t;
            sel.appendChild(opt);
        });
        setStatus(`Tablas en ${owner}: ${data.tables.length}`);
    } catch (e) {
        $("errTables").textContent = e.message;
    }
}

function applyTableFilter() {
    const q = $("tableFilter").value.toLowerCase();
    const sel = $("tables");
    [...sel.options].forEach(opt => {
        opt.hidden = q && !opt.value.toLowerCase().includes(q);
    });
}

async function loadColumns() {
    clearErr();
    const owner = $("owners").value;
    const table = $("tables").value;
    try {
        const data = await apiGet(`/meta/columns?owner=${encodeURIComponent(owner)}&table=${encodeURIComponent(table)}`);
        setOut(data);
    } catch (e) {
        $("errOutput").textContent = e.message;
    }
}

async function loadDDL() {
    clearErr();
    const owner = $("owners").value;
    const table = $("tables").value;
    try {
        const data = await apiGet(`/meta/ddl?owner=${encodeURIComponent(owner)}&table=${encodeURIComponent(table)}`);
        setOut(data.ddl || "(sin ddl / sin permisos DBMS_METADATA)");
    } catch (e) {
        $("errOutput").textContent = e.message;
    }
}

async function loadPreview() {
    clearErr();
    const owner = $("owners").value;
    const table = $("tables").value;
    try {
        const data = await apiGet(`/data/preview?owner=${encodeURIComponent(owner)}&table=${encodeURIComponent(table)}&limit=50`);
        setOut(data);
    } catch (e) {
        $("errOutput").textContent = e.message;
    }
}

$("btnConnect").onclick = async () => {
    API = $("apiBase").value.trim().replace(/\/$/, "");
    if (!API) { setStatus("Ingresá la URL del backend."); return; }
    try {
        await apiGet(`/health`);
        setStatus("Conectado ✅");
        await loadOwners();
    } catch (e) {
        setStatus(`No conecta: ${e.message}`);
    }
};

$("btnLoadTables").onclick = loadTables;
$("btnColumns").onclick = loadColumns;
$("btnDDL").onclick = loadDDL;
$("btnPreview").onclick = loadPreview;
$("tableFilter").oninput = applyTableFilter;

