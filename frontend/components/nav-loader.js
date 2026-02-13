/**
 * Zentrale Navigation Loader + Menu Toggle Functions
 * Lädt die Navigation aus /components/navigation.html
 * 
 * Usage in HTML:
 * <script src="/components/nav-loader.js"></script>
 * <script>loadNavigation('page-name');</script>
 */

const NAV_CONFIG = {
    COMPONENT_URL: '/components/navigation.html',
    SELECTORS: {
        TOGGLE: '.burger-toggle',
        MENU: 'mobile-menu',
        NAV: '.mobile-nav',
        MENU_ITEMS: '.menu-item'
    },
    ARIA: {
        OPEN: { expanded: 'true', label: 'Menü schließen' },
        CLOSED: { expanded: 'false', label: 'Menü öffnen' }
    }
};

/**
 * Close the mobile menu and update ARIA attributes
 * @param {HTMLElement} toggle - The burger toggle button
 * @param {HTMLElement} menu - The mobile menu element
 */
function closeMenu(toggle, menu) {
    menu.classList.remove('active');
    toggle.classList.remove('active');
    toggle.setAttribute('aria-expanded', NAV_CONFIG.ARIA.CLOSED.expanded);
    toggle.setAttribute('aria-label', NAV_CONFIG.ARIA.CLOSED.label);
}

/**
 * Set active menu item based on current page
 * @param {string} page - The page identifier (e.g. 'home', 'temu')
 */
function setActiveMenuItem(page) {
    const menuItems = document.querySelectorAll(NAV_CONFIG.SELECTORS.MENU_ITEMS);
    menuItems.forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-page') === page);
    });
}

/**
 * Initialize burger menu toggle and close-on-outside-click/escape
 * @param {HTMLElement} toggle - The burger toggle button
 * @param {HTMLElement} menu - The mobile menu element
 */
function initMenuBehavior(toggle, menu) {
    // Toggle menu on click
    toggle.addEventListener('click', () => {
        const isOpen = menu.classList.toggle('active');
        toggle.classList.toggle('active');
        const aria = isOpen ? NAV_CONFIG.ARIA.OPEN : NAV_CONFIG.ARIA.CLOSED;
        toggle.setAttribute('aria-expanded', aria.expanded);
        toggle.setAttribute('aria-label', aria.label);
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        const nav = document.querySelector(NAV_CONFIG.SELECTORS.NAV);
        if (nav && !nav.contains(e.target) && menu.classList.contains('active')) {
            closeMenu(toggle, menu);
        }
    });

    // Close menu with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.classList.contains('active')) {
            closeMenu(toggle, menu);
            toggle.focus();
        }
    });
}

/**
 * Load navigation from component HTML and initialize behavior
 * @param {string} currentPage - The current page identifier
 */
async function loadNavigation(currentPage = 'home') {
    try {
        const response = await fetch(NAV_CONFIG.COMPONENT_URL);
        if (!response.ok) throw new Error(`Navigation laden fehlgeschlagen: HTTP ${response.status}`);

        const html = await response.text();
        document.body.insertAdjacentHTML('afterbegin', html);

        const toggle = document.querySelector(NAV_CONFIG.SELECTORS.TOGGLE);
        const menu = document.getElementById(NAV_CONFIG.SELECTORS.MENU);

        if (toggle && menu) {
            initMenuBehavior(toggle, menu);
        }

        if (currentPage) {
            setActiveMenuItem(currentPage);
        }
    } catch (error) {
        console.error('Error loading navigation:', error);
    }
}
