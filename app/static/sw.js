// Service Worker for Car Buddies GaragePro
const CACHE_NAME = 'car-buddies-garagepro-v1.0.0';
const urlsToCache = [
    '/',
    '/static/css/styles.css',
    '/static/css/dashboard.css',
    '/static/js/app.js',
    '/static/js/pwa.js',
    '/static/js/charts.js',
    '/static/images/garage_logo.png',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png'
];

// Install event
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Return cached version or fetch from network
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});

// Activate event
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});