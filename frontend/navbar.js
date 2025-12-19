document.addEventListener('DOMContentLoaded', () => {
  try {
    const nav = document.createElement('nav');
    nav.className = 'topnav';

    const isActive = (path) => location.pathname === path;

    nav.innerHTML = `
      <div class="topnav-inner">
        <div class="brand">
          <a href="/" class="brand-link">Toci JTL Tools</a>
        </div>
        <div class="nav-links">
          <a href="/" class="nav-link ${isActive('/') ? 'active' : ''}">Start</a>
          <a href="/temu" class="nav-link ${isActive('/temu') || isActive('/temu.html') ? 'active' : ''}">TEMU Dashboard</a>
        </div>
      </div>
    `;

    document.body.prepend(nav);
  } catch (e) {
    console.error('Navbar init error:', e);
  }
});
