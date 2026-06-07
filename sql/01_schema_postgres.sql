-- =====================================================================
-- Projet : Coût de la vie et inflation au Sénégal (2018-2026)
-- Fichier : 01_schema_postgres.sql
-- Rôle    : création du modèle en étoile et chargement des données
--           (PostgreSQL ; adaptable MySQL en remplaçant COPY par LOAD DATA).
-- Source  : data/processed/*.csv (générés par le notebook 01)
-- =====================================================================

DROP SCHEMA IF EXISTS cout_vie CASCADE;
CREATE SCHEMA cout_vie;
SET search_path TO cout_vie;

-- ---------------------------------------------------------------------
-- DIMENSIONS
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    date        DATE PRIMARY KEY,
    annee       INT  NOT NULL,
    mois        INT  NOT NULL,
    mois_nom    TEXT NOT NULL,
    trimestre   TEXT NOT NULL,
    annee_mois  TEXT NOT NULL
);

CREATE TABLE dim_region (
    region      TEXT PRIMARY KEY,
    zone        TEXT,
    mult_prix   NUMERIC,
    sens_infl   NUMERIC,
    poids_zone  NUMERIC
);

CREATE TABLE dim_division (
    division_code TEXT PRIMARY KEY,
    division      TEXT NOT NULL,
    poids         INT,
    poids_frac    NUMERIC
);

CREATE TABLE dim_produit (
    produit        TEXT PRIMARY KEY,
    division_code  TEXT REFERENCES dim_division(division_code),
    categorie      TEXT,
    prix_base_2023 NUMERIC,
    unite          TEXT,
    saison_extra   NUMERIC,
    qte_panier     NUMERIC,
    administre     BOOLEAN
);

-- ---------------------------------------------------------------------
-- FAITS
-- ---------------------------------------------------------------------
CREATE TABLE fact_ihpc (
    date              DATE REFERENCES dim_date(date),
    region            TEXT REFERENCES dim_region(region),
    zone              TEXT,
    division_code     TEXT REFERENCES dim_division(division_code),
    division          TEXT,
    ponderation       NUMERIC,
    indice            NUMERIC,
    var_mensuelle_pct NUMERIC,
    var_annuelle_pct  NUMERIC,
    indice_ma3        NUMERIC
);

CREATE TABLE fact_prix (
    date              DATE REFERENCES dim_date(date),
    region            TEXT REFERENCES dim_region(region),
    produit           TEXT REFERENCES dim_produit(produit),
    division_code     TEXT,
    categorie         TEXT,
    unite             TEXT,
    prix_moyen        NUMERIC,
    var_mensuelle_pct NUMERIC,
    var_annuelle_pct  NUMERIC,
    prix_ma3          NUMERIC,
    prix_reel         NUMERIC
);

CREATE TABLE ihpc_national (
    date                     DATE PRIMARY KEY REFERENCES dim_date(date),
    indice_global            NUMERIC,
    var_mensuelle_pct        NUMERIC,
    var_annuelle_pct         NUMERIC,
    indice_alimentaire       NUMERIC,
    var_alim_annuelle_pct    NUMERIC,
    indice_energie           NUMERIC,
    var_energie_annuelle_pct NUMERIC,
    pouvoir_achat_index      NUMERIC
);

CREATE TABLE ihpc_regional (
    date             DATE,
    region           TEXT,
    zone             TEXT,
    indice_global    NUMERIC,
    var_annuelle_pct NUMERIC
);

CREATE TABLE panier_national (
    date              DATE PRIMARY KEY,
    cout_panier       NUMERIC,
    ihpc              NUMERIC,
    cout_panier_reel  NUMERIC
);

CREATE TABLE panier_regional (
    date         DATE,
    region       TEXT,
    cout_panier  NUMERIC
);

-- Index utiles aux requêtes analytiques
CREATE INDEX idx_fact_ihpc_date  ON fact_ihpc(date);
CREATE INDEX idx_fact_ihpc_div   ON fact_ihpc(division_code);
CREATE INDEX idx_fact_prix_date  ON fact_prix(date);
CREATE INDEX idx_fact_prix_prod  ON fact_prix(produit);

-- ---------------------------------------------------------------------
-- CHARGEMENT (adapter le chemin absolu vers data/processed/)
-- Note : \copy (client psql) ne nécessite pas de droits superutilisateur.
-- ---------------------------------------------------------------------
-- \copy dim_date         FROM 'data/processed/dim_date.csv'        WITH (FORMAT csv, HEADER true);
-- \copy dim_region       FROM 'data/processed/dim_region.csv'      WITH (FORMAT csv, HEADER true);
-- \copy dim_division     FROM 'data/processed/dim_division.csv'    WITH (FORMAT csv, HEADER true);
-- \copy dim_produit      FROM 'data/processed/dim_produit.csv'     WITH (FORMAT csv, HEADER true);
-- \copy fact_ihpc        FROM 'data/processed/fact_ihpc.csv'       WITH (FORMAT csv, HEADER true);
-- \copy fact_prix        FROM 'data/processed/fact_prix.csv'       WITH (FORMAT csv, HEADER true);
-- \copy ihpc_national    FROM 'data/processed/ihpc_national.csv'   WITH (FORMAT csv, HEADER true);
-- \copy ihpc_regional    FROM 'data/processed/ihpc_regional.csv'   WITH (FORMAT csv, HEADER true);
-- \copy panier_national  FROM 'data/processed/panier_national.csv' WITH (FORMAT csv, HEADER true);
-- \copy panier_regional  FROM 'data/processed/panier_regional.csv' WITH (FORMAT csv, HEADER true);
