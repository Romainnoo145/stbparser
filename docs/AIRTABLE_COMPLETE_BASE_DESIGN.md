# STB-SALES Complete Base Design - Met Koppelingen & Workflows

## 🏗️ Volledige Base Structuur

### STB-SALES Base (6 Tabellen)

1. **Klantenportaal** - Klant + offerte overzicht
2. **Elementen Overzicht** - Per element (hoofdproduct + totalen)
3. **Element Specificaties** - Doorzoekbare specs per element
4. **Subproducten** - Elke optie/toeslag apart
5. **Nacalculatie** - Kostprijs analyse per element ← **NIEUW**
6. **Projecten** - Link naar STB-PRODUCTIE base ← **TE KOPPELEN**

### ❌ Te Verwijderen
- ~~Werkorders~~ → Gaat naar STB-PRODUCTIE
- ~~Voorraad Mutaties~~ → Gaat naar STB-PRODUCTIE

---

## 📋 Tabel 1: Klantenportaal

**Functie:** Eerste overzicht van gewonnen offertes

**10 velden:**
```
Opdrachtnummer (singleLineText) [PRIMARY KEY]
Klantnaam (singleLineText)
Adres (multilineText)
Telefoon (singleLineText)
E-mail (email)
Totaalprijs Excl BTW (currency)
Totaalprijs Incl BTW (currency)
Offerte Elementen Overzicht (multilineText)
Verkoop Notities (multilineText)
Aangemaakt op (createdTime)

🔗 Linked Records:
  → Elementen (multipleRecordLinks naar Elementen Overzicht)
  → Project (singleRecordLink naar Projecten) [na inmeet]
```

**Interface View (Grid):**
```
| Opdrachtnr | Klantnaam        | Plaats      | Totaal Incl | Elementen | Project Status |
|------------|------------------|-------------|-------------|-----------|----------------|
| 2465       | Drusedau         | Hout-Blerick| €55,138     | 15        | Te Inmeten     |
| 2747       | Verhaegh         | Venlo       | €6,684      | 1         | Ingepland      |
```

**Use Case:**
- Sales team ziet alle gewonnen offertes
- Klik door naar elementen voor details
- Link naar project zodra inmeet gepland

---

## 📋 Tabel 2: Elementen Overzicht

**Functie:** Overzicht per bouwkundig element

**28 velden:**
```
# Identificatie (5)
Opdrachtnummer (singleLineText) [KEY]
Element ID (singleLineText) [PRIMARY KEY] - format: "2465-E1"
Element Volgnummer (number) - 1, 2, 3...
Klantnaam (singleLineText)
Status (singleSelect) - Te Reviewen/In Review/Goedgekeurd/Afgekeurd

# Hoofdproduct (5)
Hoofdproduct Type (singleSelect) - Deur/Raam/Schuifpui/Accessoire/Anders
Hoofdproduct Naam (singleLineText)
Hoofdproduct Beschrijving (multilineText)
Hoofdproduct Prijs Excl BTW (currency)
Hoofdproduct Aantal (number)

# Subproducten Summary (3)
Subproducten Count (number)
Subproducten Totaal Excl BTW (currency)
Heeft Hordeuren (checkbox) - formula based on linked Subproducten

# Prijzen (6)
Element Subtotaal Excl BTW (currency)
Element Korting (currency)
Element Totaal Excl BTW (currency)
Element BTW Bedrag (currency)
Element BTW Percentage (number)
Element Totaal Incl BTW (currency)

# Nacalculatie Summary (3)
Kostprijs Totaal (rollup from Nacalculatie)
Marge Euro (formula: Totaal - Kostprijs)
Marge Percentage (formula: (Totaal - Kostprijs) / Totaal * 100)

# Review & Notities (3)
Review Datum (date)
Review Door (singleLineText)
Verkoop Notities (multilineText)

🔗 Linked Records:
  → Klant (link naar Klantenportaal via Opdrachtnummer)
  → Specificaties (link naar Element Specificaties)
  → Subproducten (multipleRecordLinks)
  → Nacalculatie (link naar Nacalculatie tabel)
  → Project Element (link naar Projecten base - na inmeet)
```

**Interface Views:**

**View 1: Te Reviewen (Kanban by Status)**
```
| Te Reviewen          | In Review            | Goedgekeurd         |
|----------------------|----------------------|---------------------|
| 2465-E1 (Vast raam)  | 2465-E3 (Schuifpui) | 2465-E2 (Deur)     |
| €4,470               | €11,130              | €8,295              |
| Drusedau             | Drusedau             | Drusedau            |
```

**View 2: Per Type (Grouped)**
```
Deur (12 elementen)
  2465-E2  Voordeur met zijlicht    €8,295
  2747-E1  Dubbele tuindeur         €6,684

Schuifpui (8 elementen)
  2465-E3  Schuifpui 4-delig        €11,130

Raam (25 elementen)
  2465-E1  Vast raam                €4,470
```

**View 3: Nacalculatie Overzicht**
```
| Element ID | Type      | Verkoop | Kostprijs | Marge € | Marge % |
|------------|-----------|---------|-----------|---------|---------|
| 2465-E2    | Deur      | €8,295  | €5,200    | €3,095  | 37.3%   |
| 2465-E3    | Schuifpui | €11,130 | €7,800    | €3,330  | 29.9%   |
```

---

## 📋 Tabel 3: Element Specificaties

**Functie:** Doorzoekbare technische specs per element

**32 velden:**
```
# Identificatie (4)
Spec ID (autonumber) [PRIMARY KEY]
Element ID Ref (link naar Elementen Overzicht)
Opdrachtnummer (lookup from Element ID)
Element Type (lookup from Element ID)

# Context (3)
Element Naam (lookup from Element ID)
Klantnaam (lookup)
Locatie (singleLineText) - indien in Offorte beschrijving

# Afmetingen (3)
Geoffreerde Afmetingen (singleLineText)
Breedte (mm) (number)
Hoogte (mm) (number)

# GLAS (2)
Glas Type (singleSelect) - Triple/HR++/HR+++/Veiligheidsglas/Dubbelglas/Anders
Glas Detail (singleLineText)

# KLEUR/AFWERKING (4)
Kleur Kozijn (singleLineText)
Kleur Binnen (singleLineText)
Kleur Buiten (singleLineText)
Afwerking Type (singleSelect) - Houtnerf/Glad/Structuur/Poedercoating

# DEUR SPECIFIEK (3)
Model Deur (singleLineText)
Type Profiel/Kozijn (singleSelect)
Draairichting (singleSelect) - Links/Rechts/Dubbel

# BESLAG/HARDWARE (6)
Deurbeslag Binnen (singleLineText)
Deurbeslag Buiten (singleLineText)
Staafgreep Specificatie (singleLineText)
Scharnieren Type (singleLineText)
Type Cilinder (singleLineText)
Cilinder Gelijksluitend (singleSelect) - Ja/Nee/N.v.t.

# DORPEL/ONDERDELEN (3)
Soort Onderdorpel (singleLineText)
Brievenbus (singleSelect) - Ja/Nee/N.v.t.
Afwatering (singleSelect) - Standaard/Afwijkend/N.v.t.

# OVERIG (2)
Binnenafwerking (singleLineText)
Extra Opties (multilineText) - unparsed specs

# REVIEW (2)
Verkoop Review Status (lookup from Element)
Opmerkingen voor Binnendienst (multilineText)
```

**Interface Views:**

**View 1: Per Glas Type (Grouped)**
```
Triple (42 elementen)
  2465-E1  Vast raam         Antraciet houtnerf
  2465-E2  Voordeur          Staalblauw AP41

HR+++ (8 elementen)
  2467-E5  Schuifpui 3-delig Wit
```

**View 2: Deuren met Gelijksluitend (Filter)**
```
Filter: Element Type = "Deur" AND Cilinder Gelijksluitend = "Ja"

| Element ID | Model Deur    | Kleur Buiten | Type Cilinder |
|------------|---------------|--------------|---------------|
| 2465-E2    | Model 70      | Staalblauw   | Gelijksluit.  |
| 2465-E8    | Paneeldeur    | Antraciet    | Gelijksluit.  |
```

**View 3: Productie Planning (Calendar by Inmeetdatum)**
```
Week 41
  Mon: 2465 - 15 elementen - Triple glas - Antraciet
  Wed: 2467 - 3 elementen - HR+++ - Wit

Week 42
  Tue: 2468 - 8 elementen - Triple - Zwart
```

---

## 📋 Tabel 4: Subproducten

**Functie:** Elke optie/toeslag/accessoire als apart record

**18 velden:**
```
# Identificatie (5)
Subproduct ID (autonumber) [PRIMARY KEY]
Element ID Ref (link naar Elementen Overzicht)
Opdrachtnummer (lookup)
Klantnaam (lookup)
Element Type (lookup)

# Subproduct Info (5)
Subproduct Type (singleSelect) - Meerprijs/Optie/Accessoire/Korting
Subproduct Naam (singleLineText)
Subproduct Beschrijving (multilineText)
Subproduct Categorie (singleSelect) - Kleur/Glas/Beslag/Hordeur/Ventilatie/Dorpel/Anders
Bron (singleSelect) - Offorte/Handmatig Toegevoegd

# Prijzen (3)
Prijs Per Stuk Excl BTW (currency)
Aantal (number)
Subtotaal Excl BTW (formula)

# Offorte Meta (2)
Product ID (singleLineText) - indien aanwezig
SKU (singleLineText) - indien aanwezig

# Nacalculatie (3)
Kostprijs Per Stuk (currency) - handmatig
Kostprijs Totaal (formula)
Marge Percentage (formula)
```

**Interface Views:**

**View 1: Per Categorie (Grouped)**
```
Hordeur (23 items)
  SP-2465-E2-4  Dubbele plisse hordeur    €685   2465-E2
  SP-2467-E1-2  Enkele hordeur            €385   2467-E1

Kleur (15 items)
  SP-2465-E2-1  Meerprijs afwijkende kleur €245  2465-E2
  SP-2468-E3-1  Meerprijs structuur       €185   2468-E3
```

**View 2: Meest Verkochte Opties (Sort by Count)**
```
| Subproduct Naam                | Verkocht | Gem. Prijs | Totaal Omzet |
|--------------------------------|----------|------------|--------------|
| Dubbele plisse hordeur         | 23×      | €685       | €15,755      |
| Meerprijs afwijkende kleur     | 15×      | €240       | €3,600       |
| Afsluitbare kruk buitenzijde   | 12×      | €185       | €2,220       |
```

**View 3: Nacalculatie Subproducten**
```
Filter: Kostprijs Per Stuk IS NOT EMPTY

| Subproduct    | Verkoop | Kostprijs | Marge € | Marge % |
|---------------|---------|-----------|---------|---------|
| Plisse hordeur| €685    | €425      | €260    | 37.9%   |
| Meerprijs kleur| €245   | €95       | €150    | 61.2%   |
```

---

## 📋 Tabel 5: Nacalculatie (NIEUW)

**Functie:** Kostprijsanalyse per element met breakdown

**25 velden:**
```
# Identificatie (5)
Nacalculatie ID (autonumber) [PRIMARY KEY]
Element ID Ref (link naar Elementen Overzicht)
Opdrachtnummer (lookup)
Klantnaam (lookup)
Element Type (lookup)

# Verkoop Samenvatting (5)
Hoofdproduct Verkoop (lookup from Element)
Subproducten Verkoop (rollup from Subproducten)
Totaal Verkoop Excl BTW (formula)
Totaal Verkoop Incl BTW (lookup from Element)
Verkoop Datum (lookup from Klantenportaal)

# Kostprijs Breakdown (8)
Hoofdproduct Kostprijs (currency) - handmatig
Materiaal Kostprijs (currency) - handmatig
Arbeid Kostprijs (currency) - handmatig
Subproducten Kostprijs (rollup from Subproducten)
Transport Kosten (currency) - handmatig
Overige Kosten (currency) - handmatig
Totale Kostprijs (formula: sum all above)
Kostprijs Status (singleSelect) - Te Berekenen/Berekend/Definitief

# Marge Analyse (4)
Bruto Marge Euro (formula: Verkoop - Kostprijs)
Bruto Marge Percentage (formula)
Marge Categorie (singleSelect) - Uitstekend >40% / Goed 30-40% / Matig 20-30% / Slecht <20%
Marge Opmerking (multilineText)

# Review (3)
Nacalculatie Door (singleLineText)
Nacalculatie Datum (date)
Goedgekeurd Door (singleLineText)
```

**Interface Views:**

**View 1: Marge Dashboard (Grouped by Categorie)**
```
Uitstekend (>40%) - 12 elementen
  2465-E1  Vast raam      €4,470  →  Kostpr. €2,500  =  44.1% marge
  2465-E5  Raam           €1,307  →  Kostpr. €725    =  44.5% marge

Goed (30-40%) - 23 elementen
  2465-E2  Deur           €8,295  →  Kostpr. €5,200  =  37.3% marge

Matig (20-30%) - 8 elementen
  2465-E3  Schuifpui      €11,130 →  Kostpr. €7,800  =  29.9% marge

Slecht (<20%) - 2 elementen
  2467-E2  Accessoire     €845    →  Kostpr. €700    =  17.2% marge
```

**View 2: Kostprijs Breakdown Detail**
```
| Element | Hoofdpr. | Materiaal | Arbeid | Subprod. | Transport | Totaal |
|---------|----------|-----------|--------|----------|-----------|--------|
| 2465-E2 | €3,200   | €1,200    | €500   | €250     | €50       | €5,200 |
| 2465-E3 | €5,500   | €1,800    | €400   | €50      | €50       | €7,800 |
```

**View 3: Te Berekenen (Filter + Kanban)**
```
| Te Berekenen         | Berekend             | Definitief          |
|----------------------|----------------------|---------------------|
| 2465-E4 (Raam)       | 2465-E2 (Deur)       | 2465-E1 (Raam)     |
| Verkoop: €1,080      | Verkoop: €8,295      | Verkoop: €4,470     |
| Kostprijs: ???       | Kostprijs: €5,200    | Kostprijs: €2,500   |
|                      | Marge: 37.3%         | Marge: 44.1% ✅     |
```

---

## 📋 Tabel 6: Projecten (Link naar STB-PRODUCTIE)

**Functie:** Bridge tussen Sales en Productie

**15 velden in STB-SALES view:**
```
# Identificatie (4)
Project ID (autonumber) [PRIMARY KEY - sync from STB-PRODUCTIE]
Opdrachtnummer (singleLineText) [SYNC KEY]
Klantnaam (lookup from Klantenportaal)
Project Status (singleSelect) - Te Inmeten/Inmeet Gepland/Inmeet Voltooid/In Productie/Voltooid

# Sales Context (3)
Offerte Link (link naar Klantenportaal)
Elementen Count (rollup from Elementen Overzicht)
Totaal Verkoopprijs (lookup from Klantenportaal)

# Inmeet Planning (4)
Inmeetdatum (date)
Toegewezen Inmeter (singleSelect) - Jeroen/Donny/Anders
Inmeet Notities (multilineText)
Inmeet Voltooid (checkbox)

# Productie Status (4)
Productiestatus (sync from STB-PRODUCTIE)
Verwachte Leverdatum (date - sync from STB-PRODUCTIE)
Montage Gepland (date - sync from STB-PRODUCTIE)
Productie Notities (multilineText)

🔗 Linked Records:
  → Klant (link naar Klantenportaal)
  → Elementen (link naar Elementen Overzicht)
  → [SYNC] STB-PRODUCTIE.Projecten (cross-base sync)
```

**Interface Views:**

**View 1: Inmeet Planning (Calendar)**
```
Deze Week
  Ma 14 okt: 2465 Drusedau (15 elem.) - Jeroen
  Wo 16 okt: 2467 Neilen (8 elem.) - Donny

Volgende Week
  Ma 21 okt: 2468 Verhaegh (3 elem.) - Jeroen
```

**View 2: Status Pipeline (Kanban)**
```
| Te Inmeten    | Inmeet Gepland | Voltooid      | In Productie |
|---------------|----------------|---------------|--------------|
| 2469 (5 elem.)| 2465 (15 elem.)| 2467 (8 elem.)| 2466 (12 el.)|
| Maassen       | Drusedau       | Neilen        | Verhaegh     |
| €25,563       | €55,138        | €38,229       | €21,534      |
```

---

## 🔗 Relationele Koppelingen

### Diagram: Data Flow & Links

```
┌─────────────────────┐
│  KLANTENPORTAAL     │ ← Offorte Webhook
│  (1 per offerte)    │
└──────────┬──────────┘
           │ 1:N
           ↓
┌─────────────────────┐
│ ELEMENTEN OVERZICHT │ ← 1 record per Offorte pricetable
│ (N per offerte)     │
└─┬──────┬───────┬────┘
  │ 1:1  │ 1:N   │ 1:1
  ↓      ↓       ↓
┌────────┐ ┌──────────┐ ┌──────────────┐
│ ELEMENT│ │SUBPRODUC-│ │ NACALCULATIE │
│  SPECS │ │   TEN    │ │              │
└────────┘ └──────────┘ └──────────────┘

┌─────────────────────┐
│  KLANTENPORTAAL     │
└──────────┬──────────┘
           │ 1:1 (after inmeet)
           ↓
┌─────────────────────┐
│    PROJECTEN        │ ⟷ [SYNC] STB-PRODUCTIE.Projecten
└─────────────────────┘
```

### Link Details:

**Klantenportaal → Elementen Overzicht**
- Type: One-to-Many
- Via: Opdrachtnummer
- Display: Count of linked elements

**Elementen Overzicht → Element Specificaties**
- Type: One-to-One
- Via: Element ID
- Auto-create: Yes (bij sync)

**Elementen Overzicht → Subproducten**
- Type: One-to-Many
- Via: Element ID Ref
- Display: Count + rollup Totaal

**Elementen Overzicht → Nacalculatie**
- Type: One-to-One
- Via: Element ID Ref
- Display: Marge % in parent record

**Klantenportaal → Projecten**
- Type: One-to-One
- Via: Opdrachtnummer
- Created: After inmeet planned

---

## 🎨 Airtable Interface Designs

### Interface 1: Sales Dashboard

**Blocks:**
1. **KPI Cards**
   - Totaal Gewonnen Deze Maand
   - Gemiddelde Orderwaarde
   - Aantal Elementen Te Reviewen
   - Gemiddelde Marge %

2. **Recent Gewonnen Offertes (Table)**
   - Grid view van Klantenportaal
   - Sort: Aangemaakt op DESC
   - Limit: 10

3. **Elementen Review Status (Kanban)**
   - Grouped by Status
   - Cards: Element ID, Type, Prijs

### Interface 2: Nacalculatie Dashboard

**Blocks:**
1. **Marge Overzicht (Chart)**
   - Bar chart: Marge % per Element Type
   - Color coded: Green >40%, Yellow 30-40%, Red <20%

2. **Top/Bottom Performers (Tables)**
   - Beste Marge (top 5)
   - Slechtste Marge (bottom 5)

3. **Kostprijs Breakdown (Detail)**
   - Selected element
   - Pie chart: Materiaal, Arbeid, Subproducten, etc.

### Interface 3: Productie Planning

**Blocks:**
1. **Inmeet Calendar**
   - Calendar view by Inmeetdatum
   - Color by Inmeter

2. **Elementen Per Type (Summary)**
   - Grouped by Element Type
   - Count, Totaal Waarde

3. **Glas Bestelling Overzicht**
   - Filter: Status = Goedgekeurd
   - Group by Glas Type
   - Sum: Aantal elementen

---

## 🔄 Workflow: Van Offorte naar Productie

### Stap 1: Offorte Webhook → Klantenportaal
```
Trigger: Proposal Won
Action: Create record in Klantenportaal
```

### Stap 2: Parse Elementen
```
For each pricetable:
  - Create Elementen Overzicht record
  - Create Element Specificaties record (parsed)
  - Create Subproducten records (for option rows)
  - Create Nacalculatie record (empty, to fill)
```

### Stap 3: Sales Review
```
User: Review each element
  - Check specs in Element Specificaties
  - Verify subproducten
  - Update Status: Te Reviewen → Goedgekeurd
```

### Stap 4: Nacalculatie
```
User: Fill kostprijs in Nacalculatie
  - Hoofdproduct kostprijs
  - Materiaal, Arbeid
  - Subproducten kostprijs (linked table)
  - Review marge %
```

### Stap 5: Inmeet Planning
```
User: Create Project record
  - Link to Klantenportaal
  - Set Inmeetdatum
  - Assign Inmeter
```

### Stap 6: Sync naar STB-PRODUCTIE
```
Automation: When Inmeet Voltooid = TRUE
  - Sync Project to STB-PRODUCTIE.Projecten
  - Sync Elementen to STB-PRODUCTIE.Kozijn/Deur Elementen
  - Include Element Specificaties data
```

---

## ✅ Samenvatting: Wat Dit Oplost

### Vindbaarheid ✓
- Element Specificaties: Filter op glas, kleur, type
- Subproducten: Zoek alle hordeuren, meerprijzen
- Nacalculatie: Filter op marge categorie

### Bruikbaarheid ✓
- Nacalculatie per element + breakdown
- Productie planning via specs en inmeetdatum
- Rapportage via views en rollups

### Schaalbaarheid ✓
- Geen limieten op elementen of subproducten
- Flexibel voor variaties in Offorte data
- Uitbreidbaar met nieuwe velden

### Data Integriteit ✓
- Alle links via Element ID
- Rollups voor automatische berekeningen
- Lookups voor consistent data

### Workflow Support ✓
- Review pipeline (Te Reviewen → Goedgekeurd)
- Nacalculatie tracking
- Inmeet planning
- Sync naar Productie

---

## 📊 ImportVoorbeeld: Complete Flow

**Offorte Proposal 288976 (€45,521, 15 pricetables, 37 option rows)**

### Creates:
```
STB-SALES Base:
├── 1 Klantenportaal record
│   Opdrachtnummer: 2465
│   Klantnaam: Drusedau
│   Totaal: €55,138
│
├── 15 Elementen Overzicht records
│   2465-E1: Vast raam (€4,470)
│   2465-E2: Schuifpui 4-delig (€11,130)
│   ... (13 more)
│
├── 15 Element Specificaties records
│   2465-E1 specs: Triple glas, Antraciet, etc.
│   2465-E2 specs: Triple, Staalblauw, HST dorpel
│   ... (13 more)
│
├── 37 Subproducten records
│   SP-2465-E2-1: Afsluitbare kruk (€185 × 2)
│   SP-2465-E2-2: Plisse hordeur (€685 × 1)
│   ... (35 more)
│
└── 15 Nacalculatie records
    NAC-2465-E1: Te Berekenen
    NAC-2465-E2: Te Berekenen
    ... (13 more)

TOTAAL: 83 Airtable records
```

### Later (after review):
```
STB-SALES:
└── 1 Projecten record
    PRJ-2465: Drusedau
    Inmeet: 14 okt 2025
    Inmeter: Jeroen
    Status: Inmeet Gepland

                ↓ [SYNC AFTER INMEET VOLTOOID]

STB-PRODUCTIE Base:
└── 1 Projecten record (synced)
    └── 15 Kozijn/Deur Elementen (synced)
```

---

## ❓ Beslissingen Nodig

1. **Base structuur akkoord?**
   - 6 tabellen: Klantenportaal, Elementen Overzicht, Element Specificaties, Subproducten, Nacalculatie, Projecten

2. **Nacalculatie tabel velden?**
   - Breakdown: Hoofdproduct, Materiaal, Arbeid, Subproducten, Transport, Overige
   - Is dit voldoende of meer detail nodig?

3. **Projecten sync naar STB-PRODUCTIE?**
   - Manual of automatic?
   - Welke velden moeten syncen?

4. **Verwerkingen/Formules?**
   - Welke berekeningen moeten automatic zijn?
   - Welke handmatig te vullen?

