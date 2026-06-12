const CACHE_NAME = 'oxu-career-v1';
const ASSETS = [
  '/',
  '/manifest.json'
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Активация
self.addEventListener('activate', (event) => {
  console.log('Service Worker активирован');
});

// Обработка запросов (Fetch)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});