// Fallback catalog export that runs in your browser (use it only if pipeline/build_catalog.py
// cannot reach the PSI API from Python).
//
// 1. Open https://psi.nasa.gov/physci/repo/search?q=combustion in Chrome or Edge.
// 2. Open DevTools (F12) -> Console, paste this whole file, press Enter.
// 3. Wait for "done" (about 1-2 minutes). The browser saves psi_catalog_bundle.json.
// 4. In the repo: python -m pipeline.import_bundle path/to/psi_catalog_bundle.json
//
// It calls the same endpoints as the PSI web app and the Python client. Nothing is sent anywhere else.
(async (opts = {}) => {
  const term = opts.term || "combustion";
  const skip = new Set(opts.skip || ["PSI-181", "PSI-108"]); // matched the search word, not combustion
  const only = opts.only ? new Set(opts.only) : null;
  const save = opts.save !== false;
  const api = "/geode-py/ws";
  const log = (...a) => console.log("[psi-export]", ...a);

  const search = await fetch(`${api}/repo/search?term=${encodeURIComponent(term)}&source=psi&type=investigation&size=200&from=0`).then(r => r.json());
  const hits = search.hits.hits.map(h => h._source);
  const ids = hits.map(h => h.Accession).filter(id => !skip.has(id) && (!only || only.has(id)));
  log(`${hits.length} hits, exporting ${ids.length}`);

  const flatten = (nodes, out = []) => {
    for (const n of nodes || []) {
      if (n.directory === false) out.push([n.key, n.bytes_size || 0, n.version || 1]);
      else flatten(n.files, out);
    }
    return out;
  };

  const bundle = { term, exported_at: new Date().toISOString(), investigations: [] };
  for (const id of ids) {
    const meta = await fetch(`${api}/repo/investigations/${id}`).then(r => r.json());
    delete meta.added; delete meta.removed; delete meta.modified; // file-history lists the catalog does not use
    const tree = await fetch(`${api}/files/v2`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: `psi-data/${id}/`, fileType: "study", studyId: id, version: meta.version || 1 }),
    }).then(r => r.json());
    const files = flatten(tree.files);
    const tables = [];
    for (const [key, , version] of files.filter(f => /\/Experimental table\/.*\.csv$/.test(f[0]))) {
      const name = key.split("/").pop();
      const url = await fetch(`${api}/studies/${id}/download?file=${encodeURIComponent(name)}&version=${version}&redirect=false`).then(r => r.text());
      const res = await fetch(url.trim());
      tables.push({ key, name, status: res.status, text: res.ok ? await res.text() : "" });
    }
    bundle.investigations.push({ id, hit: hits.find(h => h.Accession === id), meta, files, tables });
    log(`${id} ${meta.investigationAcronym || ""}: ${files.length} files, ${tables.length} tables`);
  }

  const json = JSON.stringify(bundle);
  if (save) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    a.download = "psi_catalog_bundle.json";
    a.click();
  }
  log(`done: ${bundle.investigations.length} investigations, ${(json.length / 1e6).toFixed(1)} MB`);
  return save ? "saved" : json;
})(window.__psiExportOptions || {});
