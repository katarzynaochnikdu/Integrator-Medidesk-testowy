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
})();
