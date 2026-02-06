/**
 * Zentrale Navigation Loader + Menu Toggle Functions
 * Lädt die Navigation aus /components/navigation.html
 * 
 * Usage in HTML:
 * <script src="/components/nav-loader.js"></script>
 * <script>loadNavigation('page-name', 'Page Title');</script>
 */

// Toggle Menu Function
function toggleMenu() {
    const menu = document.getElementById('mobile-menu');
    const toggle = document.querySelector('.burger-toggle');
    if (menu && toggle) {
        menu.classList.toggle('active');
        toggle.classList.toggle('active');
    }
}

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    const nav = document.querySelector('.mobile-nav');
    const menu = document.getElementById('mobile-menu');
    const toggle = document.querySelector('.burger-toggle');

    if (nav && !nav.contains(e.target) && menu && menu.classList.contains('active')) {
        menu.classList.remove('active');
        toggle.classList.remove('active');
    }
});

// Set active menu item based on current page
function setActiveMenuItem(page) {
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Load navigation from component
async function loadNavigation(currentPage = 'home') {
    try {
        const response = await fetch('/components/navigation.html');
        if (!response.ok) throw new Error('Failed to load navigation');
        
        const html = await response.text();
        
        // Insert at beginning of body
        document.body.insertAdjacentHTML('afterbegin', html);

        // Set active menu item
        if (currentPage) {
            setTimeout(() => {
                setActiveMenuItem(currentPage);
            }, 10);
        }
    } catch (error) {
        console.error('Error loading navigation:', error);
    }
}
