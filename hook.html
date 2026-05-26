/**
 * FAFNIR CORE RESILIENCE ENGINE
 * Global utilities for Frontend-Backend Sync
 */

window.Fafnir = {
    failCount: 0,
    
    // --- Fail-Safe Fetch Mechanism ---
    async safeFetch(url, options = {}, retries = 2) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data && data.error) console.warn("API Warning:", data.error);
            this.failCount = 0;
            return data;
        } catch (e) {
            console.error(`Fetch failed for ${url}:`, e);
            if (retries > 0) {
                // Exponential backoff
                const delay = (3 - retries) * 1000;
                await new Promise(r => setTimeout(r, delay));
                return this.safeFetch(url, options, retries - 1);
            }
            this.failCount++;
            throw e;
        }
    },

    // --- Global Connection Status Manager ---
    updateStatusUI(status = 'Online') {
        const st = document.getElementById('stxt');
        if (!st) return;
        
        if (status === 'Online') {
            st.textContent = 'Online';
            st.className = "uppercase tracking-wider text-green-400";
            if (st.previousElementSibling) {
                st.previousElementSibling.className = "w-2 h-2 rounded-full animate-pulse shadow-[0_0_10px_currentColor] bg-green-400";
            }
        } else if (status === 'Reconnecting') {
            st.textContent = 'Reconnecting...';
            st.className = "uppercase tracking-wider text-yellow-400";
            if (st.previousElementSibling) {
                st.previousElementSibling.className = "w-2 h-2 rounded-full bg-yellow-500 shadow-[0_0_10px_currentColor]";
            }
        } else {
            st.textContent = 'Offline';
            st.className = "uppercase tracking-wider text-red-400";
            if (st.previousElementSibling) {
                st.previousElementSibling.className = "w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_currentColor]";
            }
        }
    },

    // --- Cold Start Trigger ---
    async pokeServer() {
        try {
            await fetch('/api/ping');
        } catch(e) {}
    }
};

// Auto-poke server on load to ensure it's awake
window.addEventListener('DOMContentLoaded', () => {
    window.Fafnir.pokeServer();
});
