// Rechargement du planning : onUpdate seulement quand la version change, onStatus à chaque tentative.
export function createPlanningSource({
  url, intervalMs = 60000, fetchFn = (...args) => fetch(...args), onUpdate, onStatus,
}) {
  let lastVersion = null;
  let timer = null;

  async function pollNow() {
    try {
      const res = await fetchFn(url, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const planning = await res.json();
      // le service worker marque les réponses servies depuis son cache (réseau indisponible)
      onStatus(res.headers?.get?.('x-sw-cache') ? 'offline' : 'online');
      if (planning.version !== lastVersion) {
        lastVersion = planning.version;
        onUpdate(planning);
      }
    } catch {
      onStatus('offline');
    }
  }

  return {
    pollNow,
    start() {
      pollNow();
      timer = setInterval(pollNow, intervalMs);
    },
    stop() {
      clearInterval(timer);
      timer = null;
    },
  };
}
