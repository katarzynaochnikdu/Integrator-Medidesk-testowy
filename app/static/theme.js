/**
 * Mechanizm wykrywania i aplikowania trybu wyświetlania przed załadowaniem DOM.
 * Rozwiązuje problem "błysku białego tła" na start przy wybranym Dark Mode.
 */
(function() {
    function getTheme() {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    document.documentElement.setAttribute('data-theme', getTheme());

    // Wyeksponuj pod API do przełączania go z UI
    window.setAppTheme = function(theme) {
        if (theme === 'system') {
            localStorage.removeItem('theme');
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        } else {
            localStorage.setItem('theme', theme);
            document.documentElement.setAttribute('data-theme', theme);
        }
    };

    // Globalny handler Escape — zamyka otwarte modale.
    // Lista modali do zamknięcia (w kolejności priorytetu). Pomijamy #app-dialog-overlay —
    // ma własny handler w dashboard.html (z obsługą Enter/resolvera).
    const MODAL_SELECTORS = [
        { sel: '#test-flow-modal',    close: (el) => { el.style.display = 'none'; } },
        { sel: '#edit-mappings-modal', close: (el) => { el.style.display = 'none'; } },
        { sel: '#confirm-exit-modal', close: (el) => { el.classList.remove('open'); } },
    ];

    function isVisible(el) {
        if (!el) return false;
        // Obsługa obu wzorców: inline display:flex oraz klasa .open
        if (el.classList && el.classList.contains('open')) return true;
        const disp = (el.style && el.style.display) || '';
        if (disp && disp !== 'none') return true;
        return false;
    }

    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Escape') return;
        // Jeśli aktywny jest app-dialog, oddaj mu pierwszeństwo
        const appDialog = document.getElementById('app-dialog-overlay');
        if (appDialog && appDialog.style.display !== 'none') return;
        // Nie zamykaj gdy user właśnie pisze w kontrolce z otwartym natywnym dropdownem — natywny select sam łapie Escape.
        // Zamknij pierwszy widoczny modal z listy.
        for (const { sel, close } of MODAL_SELECTORS) {
            const el = document.querySelector(sel);
            if (isVisible(el)) {
                e.preventDefault();
                close(el);
                return;
            }
        }
    });
})();
