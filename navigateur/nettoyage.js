// Nettoyage hebdomadaire des cookies de pistage (extension Chrome, Manifest V3).
// Règle : un cookie est effacé si son domaine figure dans la liste des pisteurs de Disconnect (publicité, mesure
// d'audience, empreinte, réseaux sociaux, pistage par mail, minage) ET si l'utilisateur n'a jamais visité ce site
// lui-même ces 90 derniers jours. Les sites qu'il visite (Google, LinkedIn, sa banque…) gardent leurs cookies, donc
// ses connexions. La liste est téléchargée à chaque passe depuis le dépôt public de Disconnect (licence CC BY-NC-SA 4.0,
// non recopiée ici) ; si elle est injoignable, rien n'est effacé.
const LISTE = "https://raw.githubusercontent.com/disconnectme/disconnect-tracking-protection/master/services.json";
const CATEGORIES = ["Advertising", "Analytics", "FingerprintingInvasive", "FingerprintingGeneral", "Social",
                    "Email", "EmailAggressive", "Cryptomining"];   // pas « Content », « Anti-fraud », « ConsentManagers »
const SEMAINE = 7 * 24 * 60;
const SUFFIXES_DOUBLES = /\.(co|com|org|net|gov|gouv|ac|edu|ne|or)\.[a-z]{2}$/;

function racine(hote) {   // domaine enregistrable, approché : exemple.fr, exemple.co.uk
  const h = hote.replace(/^\./, "").toLowerCase();
  const p = h.split(".");
  return p.slice(SUFFIXES_DOUBLES.test(h) ? -3 : -2).join(".");
}

async function pisteurs() {
  const r = await fetch(LISTE, {cache: "no-store"});
  if (!r.ok) throw new Error("liste " + r.status);
  const d = await r.json();
  const s = new Set();
  for (const cat of CATEGORIES)
    for (const entree of d.categories[cat] || [])
      for (const service of Object.values(entree))
        for (const doms of Object.values(service))
          if (Array.isArray(doms)) doms.forEach(x => s.add(x.toLowerCase()));
  return s;
}

async function visites() {
  const debut = Date.now() - 90 * 24 * 3600 * 1000;
  const h = await chrome.history.search({text: "", startTime: debut, maxResults: 100000});
  const s = new Set();
  for (const x of h) { try { s.add(racine(new URL(x.url).hostname)); } catch (e) {} }
  return s;
}

function estPisteur(dom, liste) {
  const d = dom.replace(/^\./, "").toLowerCase();
  for (let x = d; x.includes("."); x = x.slice(x.indexOf(".") + 1)) if (liste.has(x)) return true;
  return false;
}

async function tousLesCookies() {
  const a = await chrome.cookies.getAll({});
  let b = [];
  try { b = await chrome.cookies.getAll({partitionKey: {}}); } catch (e) {}   // cookies partitionnés (CHIPS)
  const vus = new Set(), tout = [];
  for (const c of a.concat(b)) {
    const k = [c.domain, c.path, c.name, c.storeId, JSON.stringify(c.partitionKey || null)].join("|");
    if (!vus.has(k)) { vus.add(k); tout.push(c); }
  }
  return tout;
}

async function nettoyer() {
  let liste;
  try { liste = await pisteurs(); }
  catch (e) { await chrome.storage.local.set({erreur: String(e)}); return null; }
  const garder = await visites();
  const parDomaine = {};
  let n = 0;
  for (const c of await tousLesCookies()) {
    if (!estPisteur(c.domain, liste) || garder.has(racine(c.domain))) continue;
    const details = {url: (c.secure ? "https://" : "http://") + c.domain.replace(/^\./, "") + c.path,
                     name: c.name, storeId: c.storeId};
    if (c.partitionKey) details.partitionKey = c.partitionKey;
    if (await chrome.cookies.remove(details)) {
      n++; const r = racine(c.domain); parDomaine[r] = (parDomaine[r] || 0) + 1;
    }
  }
  const passe = {date: new Date().toISOString(), effaces: n, domaines: parDomaine};
  const {passes = []} = await chrome.storage.local.get("passes");
  await chrome.storage.local.set({passes: [passe, ...passes].slice(0, 12), erreur: null});
  return passe;
}

async function siDu() {   // au démarrage du navigateur : rattrape une passe manquée (ordinateur éteint)
  const {passes = []} = await chrome.storage.local.get("passes");
  if (!passes.length || Date.now() - Date.parse(passes[0].date) > SEMAINE * 60 * 1000) await nettoyer();
}

chrome.runtime.onInstalled.addListener(() => { chrome.alarms.create("semaine", {periodInMinutes: SEMAINE}); siDu(); });
chrome.runtime.onStartup.addListener(siDu);
chrome.alarms.onAlarm.addListener(a => { if (a.name === "semaine") nettoyer(); });
chrome.runtime.onMessage.addListener((m, _, repondre) => {
  if (m === "nettoyer") { nettoyer().then(repondre); return true; }
});
