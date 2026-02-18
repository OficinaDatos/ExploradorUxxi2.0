let API = "";
const $ = (id) => document.getElementById(id);

function setStatus(msg) { $("status").textContent = msg; }

// Transforma JSON en una tabla HTML real
function setOut(obj) {
    const output = $("output");
    output.innerHTML = ""; 

    const rows = obj.rows || (Array.isArray(obj) ? obj : null);

    if (rows && rows.length > 0) {
        const table = document.createElement("table");
        table.className = "data-table";
        
        // Encabezados
        const headers = Object.keys(rows[0]);
        const trH = document.createElement("tr");
        headers.forEach(h => {
            const th = document.createElement("th");
            th.textContent = h;
            trH.appendChild(th);
        });
        table.appendChild(trH);

        // Filas
        rows.forEach(row => {
            const tr = document.createElement("tr");
            headers.forEach(h => {
                const td = document.createElement("td");
                td.textContent = row[h];
                tr.appendChild(td);
            });
            table.appendChild(tr);
        });
        output.appendChild(table);
    } else {
        output.textContent = JSON.stringify(obj, null, 2);
    }
}

async function apiGet(path) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error en la petición");
    }
    return await res.json();
}

async function loadOwners() {
    try {
        const data = await apiGet(`/meta/owners`);
        const sel = $("owners");
        sel.innerHTML = "";
        data.owners.forEach(o => {
            const opt = document.createElement("option");
            opt.value = o; opt.textContent = o;
            sel.appendChild(opt);
        });
        setStatus(`Owners cargados: ${data.owners.length}`);
    } catch (e) { setStatus("Error al cargar owners"); }
}

async function loadTables() {
    const owner = $("owners").value;
    try {
        const data = await apiGet(`/meta/tables?owner=${encodeURIComponent(owner)}`);
        const sel = $("tables");
        sel.innerHTML = "";
        data.tables.forEach(t => {
            const opt = document.createElement("option");
            opt.value = t; opt.textContent = t;
            sel.appendChild(opt);
        });
        setStatus(`Tablas/Vistas en ${owner}: ${data.tables.length}`);
    } catch (e) { setStatus("Error al cargar tablas"); }
}

async function loadPreview() {
    const owner = $("owners").value;
    const table = $("tables").value;
    setStatus("Cargando datos...");
    try {
        const data = await apiGet(`/data/preview?owner=${encodeURIComponent(owner)}&table=${encodeURIComponent(table)}&limit=50`);
        setOut(data);
        setStatus("Datos cargados ✅");
    } catch (e) { setStatus("Error al cargar datos"); }
}

$("btnConnect").onclick = async () => {
    API = $("apiBase").value.trim().replace(/\/$/, "");
    await loadOwners();
};

$("btnLoadTables").onclick = loadTables;
$("btnPreview").onclick = loadPreview;


