// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;
const installButton = document.getElementById('install-button');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    // Show install button if it exists
    if (installButton) {
        installButton.style.display = 'block';
        installButton.addEventListener('click', installApp);
    }
});

async function installApp() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
        }
        deferredPrompt = null;
        if (installButton) {
            installButton.style.display = 'none';
        }
    }
}

// Network Status Detection
window.addEventListener('online', function() {
    showAlert('Connection restored', 'success');
    // Sync any pending operations
    syncPendingOperations();
});

window.addEventListener('offline', function() {
    showAlert('You are currently offline', 'warning', 0);
});

function syncPendingOperations() {
    // Sync any data that was saved while offline
    // This would depend on your specific offline storage implementation
    console.log('Syncing pending operations...');
}