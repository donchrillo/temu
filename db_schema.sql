-- Datenbank erstellen (falls nicht vorhanden)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'toci')
BEGIN
    CREATE DATABASE toci;
END
GO

USE toci;
GO

-- Tabelle für Bestellungen (Header-Daten)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'temu_orders')
BEGIN
    CREATE TABLE temu_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        bestell_id NVARCHAR(50) NOT NULL UNIQUE,
        bestellstatus NVARCHAR(50),
        kaufdatum DATETIME,
        
        -- Empfänger
        name_empfaenger NVARCHAR(200),
        vorname_empfaenger NVARCHAR(100),
        nachname_empfaenger NVARCHAR(100),
        telefon_empfaenger NVARCHAR(50),
        email NVARCHAR(255),
        
        -- Adresse
        strasse NVARCHAR(200),
        adresszusatz NVARCHAR(200),
        plz NVARCHAR(20),
        ort NVARCHAR(100),
        bundesland NVARCHAR(100),
        land NVARCHAR(50),
        land_iso NVARCHAR(2),
        
        -- Versand
        versandkosten DECIMAL(10,2),
        versanddienstleister NVARCHAR(100) NULL,
        trackingnummer NVARCHAR(100) NULL,
        versanddatum DATETIME NULL,
        
        -- Status
        status NVARCHAR(50) DEFAULT 'importiert',
        xml_erstellt BIT DEFAULT 0,
        temu_gemeldet BIT DEFAULT 0,
        
        -- Status-Flow:
        -- 'importiert' -> Neue Bestellung aus TEMU CSV
        -- 'xml_erstellt' -> XML wurde erstellt und an JTL übergeben
        -- 'versendet' -> Trackingnummer aus JTL erhalten
        -- 'storniert' -> Von TEMU storniert (wird NICHT nach JTL exportiert)
        
        -- Timestamps
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_bestell_id ON temu_orders(bestell_id);
    CREATE INDEX idx_status ON temu_orders(status);
    CREATE INDEX idx_trackingnummer ON temu_orders(trackingnummer);
END
GO

-- Tabelle für Bestellpositionen (Artikel)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'temu_order_items')
BEGIN
    CREATE TABLE temu_order_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id INT NOT NULL,
        bestell_id NVARCHAR(50) NOT NULL,
        bestellartikel_id NVARCHAR(50) NOT NULL UNIQUE,
        
        -- Artikel
        produktname NVARCHAR(500),
        sku NVARCHAR(100),
        sku_id NVARCHAR(100),
        variation NVARCHAR(200),
        
        -- Mengen & Preise
        menge DECIMAL(10,2),
        netto_einzelpreis DECIMAL(10,2),
        brutto_einzelpreis DECIMAL(10,2),
        gesamtpreis_netto DECIMAL(10,2),
        gesamtpreis_brutto DECIMAL(10,2),
        mwst_satz DECIMAL(5,2) DEFAULT 19.00,
        
        -- Timestamps
        created_at DATETIME DEFAULT GETDATE(),
        
        FOREIGN KEY (order_id) REFERENCES temu_orders(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_order_id ON temu_order_items(order_id);
    CREATE INDEX idx_bestellartikel_id ON temu_order_items(bestellartikel_id);
    CREATE INDEX idx_bestell_id ON temu_order_items(bestell_id);
END
GO

-- Tabelle für XML-Export (für JTL Worker)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'temu_xml_export')
BEGIN
    CREATE TABLE temu_xml_export (
        id INT IDENTITY(1,1) PRIMARY KEY,
        bestell_id NVARCHAR(50) NOT NULL,
        xml_content NVARCHAR(MAX) NOT NULL,
        status NVARCHAR(50) DEFAULT 'pending',
        verarbeitet BIT DEFAULT 0,
        created_at DATETIME DEFAULT GETDATE(),
        processed_at DATETIME NULL
    );
    
    CREATE INDEX idx_status ON temu_xml_export(status);
    CREATE INDEX idx_bestell_id ON temu_xml_export(bestell_id);
END
GO

-- Tabelle für Produkt-Mapping (TEMU SKU <-> JTL Artikel)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'temu_products')
BEGIN
    CREATE TABLE temu_products (
        id INT IDENTITY(1,1) PRIMARY KEY,
        sku NVARCHAR(100) NOT NULL UNIQUE,     -- TEMU skuSn = JTL SKU
        goods_id BIGINT NOT NULL,              -- Warennummer (Parent/Single)
        sku_id BIGINT NULL,                    -- TEMU skuId (Child/Single, NULL für Parent)
        goods_name NVARCHAR(500) NULL,         -- Optional: TEMU Titel
        jtl_article_id INT NULL,               -- via SKU in JTL gemappt
        is_active BIT DEFAULT 1,
        synced_at DATETIME NULL,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX idx_temu_products_goods_id ON temu_products(goods_id);
    CREATE INDEX idx_temu_products_jtl_article_id ON temu_products(jtl_article_id);
END
GO

-- Tabelle für Bestände (TEMU <-> JTL)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'temu_inventory')
BEGIN
    CREATE TABLE temu_inventory (
        id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        jtl_article_id INT NULL,
        jtl_stock INT NOT NULL DEFAULT 0,
        temu_stock INT NOT NULL DEFAULT 0,
        needs_sync BIT NOT NULL DEFAULT 0,      -- TRUE, wenn JTL != TEMU
        last_synced_to_temu DATETIME NULL,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (product_id) REFERENCES temu_products(id) ON DELETE CASCADE
    );
    CREATE INDEX idx_temu_inventory_product_id ON temu_inventory(product_id);
    CREATE INDEX idx_temu_inventory_needs_sync ON temu_inventory(needs_sync);
END
GO
