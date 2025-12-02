-- Datenbank erstellen (falls nicht vorhanden)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'TemuOrders')
BEGIN
    CREATE DATABASE TemuOrders;
END
GO

USE TemuOrders;
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
