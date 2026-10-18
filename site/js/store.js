// Stockage local ; si localStorage est indisponible (mode privé, quota), on garde en mémoire.
const KEYS = { person: 'stunindie.person', fired: 'stunindie.fired', seen: 'stunindie.seen' };
const memory = new Map();

function read(key) {
  try {
    const v = localStorage.getItem(key);
    if (v !== null) return v;
  } catch { /* stockage indisponible */ }
  return memory.get(key) ?? null;
}

function write(key, value) {
  memory.set(key, value);
  try { localStorage.setItem(key, value); } catch { /* stockage indisponible */ }
}

function remove(key) {
  memory.delete(key);
  try { localStorage.removeItem(key); } catch { /* stockage indisponible */ }
}

function readJson(key) {
  try { return JSON.parse(read(key)); } catch { return null; }
}

export const getSlug = () => read(KEYS.person);
export const setSlug = (slug) => write(KEYS.person, slug);
export const clearSlug = () => remove(KEYS.person);

export const getFired = () => new Set(readJson(KEYS.fired) ?? []);
export function addFired(key) {
  const fired = getFired();
  fired.add(key);
  write(KEYS.fired, JSON.stringify([...fired]));
}

// Dernier planning vu, par personne : { version, blocks } (pour la bannière de mise à jour)
export const getSeen = (slug) => (readJson(KEYS.seen) ?? {})[slug] ?? null;
export function setSeen(slug, seen) {
  write(KEYS.seen, JSON.stringify({ ...(readJson(KEYS.seen) ?? {}), [slug]: seen }));
}
