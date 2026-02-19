/**
 * ERP Sidebar Navigation
 * Verwaltet alle Navigationseinträge für das ERP-System
 */

const ERP_SIDEBAR = {
    sections: [
        {
            id: 'admin',
            label: 'Verwaltung',
            icon: '⚙️',
            items: [
                { id: 'connector', label: 'TEMU Connector', path: '/temu', active: true },
                { id: 'marketplaces', label: 'Marktplätze', path: '/marketplaces', disabled: true }
            ]
        },
        {
            id: 'tools',
            label: 'Werkzeuge',
            icon: '🔧',
            items: [
                { id: 'csv', label: 'CSV-Verarbeiter', path: '/csv', active: true },
                { id: 'pdf', label: 'PDF-Reader', path: '/pdf', active: true }
            ]
        },
        {
            id: 'crm',
            label: 'Kunden',
            icon: '👥',
            items: [
                { id: 'customers', label: 'Kundenverwaltung', path: '/customers', disabled: true }
            ]
        },
        {
            id: 'pim',
            label: 'Artikel',
            icon: '📦',
            items: [
                { id: 'products', label: 'Artikelliste', path: '/products', disabled: true },
                { id: 'categories', label: 'Kategorien', path: '/categories', disabled: true }
            ]
        },
        {
            id: 'oms',
            label: 'Aufträge',
            icon: '📋',
            items: [
                { id: 'orders', label: 'Bestellungen', path: '/orders', disabled: true },
                { id: 'returns', label: 'Retouren', path: '/returns', disabled: true }
            ]
        },
        {
            id: 'wms',
            label: 'Lager & Versand',
            icon: '🚚',
            items: [
                { id: 'picklists', label: 'Picklisten', path: '/picklists', disabled: true },
                { id: 'packstation', label: 'Packtisch', path: '/packstation', disabled: true },
                { id: 'inventory', label: 'Bestand', path: '/inventory', disabled: true }
            ]
        }
    ],
    
    /**
     * Render die Sidebar in einen Container
     * @param {string} containerId - ID des Container-Elements
     */
    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Sidebar container #${containerId} not found`);
            return;
        }
        
        let html = '<nav class="erp-nav">';
        
        for (const section of this.sections) {
            html += `
            <div class="nav-section">
                <div class="nav-section-header">
                    <span class="nav-icon">${section.icon}</span>
                    <span class="nav-label">${section.label}</span>
                </div>
                <ul class="nav-items">`;
            
            for (const item of section.items) {
                const isDisabled = item.disabled ? 'disabled' : '';
                const isActive = item.active ? 'active' : '';
                const target = item.disabled ? '' : `href="${item.path}"`;
                
                html += `
                <li class="nav-item ${isDisabled} ${isActive}">
                    <a ${target}>${item.label}</a>
                </li>`;
            }
            
            html += '</ul></div>';
        }
        
        html += '</nav>';
        container.innerHTML = html;
    },
    
    /**
     * Markiere einen Navigationspunkt als aktiv
     * @param {string} itemId - ID des Items
     */
    setActive(itemId) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.classList.contains(itemId)) {
                item.classList.add('active');
            }
        });
    }
};

// Export for global use
window.ERP_SIDEBAR = ERP_SIDEBAR;
