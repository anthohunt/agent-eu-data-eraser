const t = (k, ...a) => chrome.i18n.getMessage(k, a.map(String));
async function afficher() {
  const {passes = [], erreur} = await chrome.storage.local.get(["passes", "erreur"]);
  const p = passes[0];
  document.getElementById("etat").textContent = erreur ? t("erreur") :
    p ? t("dernier", new Date(p.date).toLocaleDateString(), p.effaces) : t("jamais");
  const ul = document.getElementById("liste"); ul.textContent = "";
  for (const [d, n] of Object.entries(p ? p.domaines : {}).sort((a, b) => b[1] - a[1]).slice(0, 15)) {
    const li = document.createElement("li"); li.textContent = `${d} (${n})`; ul.appendChild(li);
  }
  document.getElementById("prochain").textContent = t("prochain");
}
const b = document.getElementById("go");
b.textContent = t("maintenant");
b.onclick = async () => { b.disabled = true; b.textContent = t("encours");
  await chrome.runtime.sendMessage("nettoyer"); b.disabled = false; b.textContent = t("maintenant"); afficher(); };
afficher();
