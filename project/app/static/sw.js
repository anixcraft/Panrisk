// Network-first for the app shell (offline fallback). Health data under /api/ is NEVER cached.
const CACHE='pancrisk-shell-v1';
const SHELL=['/','/style.css','/app.js','/manifest.webmanifest','/icon-192.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET'||u.pathname.startsWith('/api/'))return;
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
