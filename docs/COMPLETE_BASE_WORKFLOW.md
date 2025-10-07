# Complete Workflow: 3 Bases & Data Flow

## 🏢 Base Overzicht & Flow

```
┌──────────────────────────────────────────────────────────────┐
│  1. STB-SALES (Verkoop & Review)                            │
│     - Klantenportaal                                         │
│     - Elementen Overzicht                                    │
│     - Element Specificaties                                  │
│     - Subproducten                                           │
│     - Nacalculatie                                           │
└────────────────────┬─────────────────────────────────────────┘
                     │ DIRECT SYNC (na offerte won)
                     ↓
┌──────────────────────────────────────────────────────────────┐
│  2. STB-ADMINISTRATIE (Facturatie & Inmeet Planning)        │
│     - Facturatie (3 facturen: 30%/65%/5%)                   │
│     - Inmeetplanning (planning & status)                     │
│     - [NIEUWE] Projecten (central project record)           │
└────────────────────┬─────────────────────────────────────────┘
                     │ SYNC (na inmeet voltooid)
                     ↓
┌──────────────────────────────────────────────────────────────┐
│  3. STB-PRODUCTIE (Productie & Montage)                     │
│     - Projecten                                              │
│     - Kozijn Elementen                                       │
│     - Deur Elementen                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Herzien: STB-SALES Structuur

### Tabel 1-5: ONGEWIJZIGD
(Klantenportaal, Elementen Overzicht, Element Specificaties, Subproducten, Nacalculatie)

### ❌ Tabel 6: Projecten VERWIJDEREN uit STB-SALES

**Reden:** Project record hoort in STB-ADMINISTRATIE als centrale plek

---

## 📋 Herzien: STB-ADMINISTRATIE Structuur

### Bestaande Tabellen:

#### 1. Facturatie (12 velden) - BEHOUDEN
```
Factuur ID [key]
Opdrachtnummer
Type Factuur (30% Vooraf / 65% Start / 5% Oplevering)
Bedrag (currency)
Status (Concept / Verzonden / Betaald)
Verstuurd op (dateTime)
Vervaldatum (date)
Klant (singleLineText)
Email
Telefoon
Adres
Factuurtitel
```

#### 2. Inmeetplanning (23 velden) - BEHOUDEN
```
Opdrachtnummer [key]
Klant & Stad
Telefoon
Elementen (number)
Uren (number)
Waarde (currency)
Projectstatus (Planning Vereist / Ingepland / Voltooid)
Klantnaam
E-mail
Volledig Adres
Stad, Postcode, Provincie
Opdracht verkocht op
Total Amount Incl BTW
Aantal Elementen
Elementen Overzicht (multilineText)
Locaties (multilineText)
Geschatte Uren
Planning Notities
Uiterlijke montagedatum
Inmeetdatum
Start Inmeetplanning Trigger (checkbox)
```

### 🆕 Nieuwe Tabel: Projecten (CENTRAL HUB)

**Functie:** Central project record, links alle 3 bases

**28 velden:**
```
# Identificatie (5)
Project ID (autonumber) [PRIMARY KEY]
Opdrachtnummer (singleLineText) [SYNC KEY - alle bases]
Klantnaam (singleLineText)
Project Status (singleSelect) - Nieuw/Facturatie/Inmeet Planning/Inmeet Voltooid/In Productie/Voltooid
Aangemaakt op (createdTime)

# Klant Info (5)
Volledig Adres (multilineText)
Postcode (singleLineText)
Stad (singleLineText)
Telefoon (singleLineText)
Email (email)

# Sales Context (6)
Totaal Verkoopprijs Excl BTW (currency)
Totaal Verkoopprijs Incl BTW (currency)
Aantal Elementen (number)
Elementen Samenvatting (multilineText)
Verkoop Review Status (singleSelect) - In Review/Goedgekeurd/Afgekeurd
Verkoop Notities (multilineText)

# Facturatie (3)
Factuur 30% Status (lookup from Facturatie)
Factuur 65% Status (lookup from Facturatie)
Factuur 5% Status (lookup from Facturatie)

# Inmeet (5)
Inmeet Status (lookup from Inmeetplanning)
Inmeetdatum (lookup from Inmeetplanning)
Toegewezen Inmeter (lookup from Inmeetplanning)
Inmeet Notities (multilineText)
Inmeet Voltooid (checkbox)

# Productie (4)
Productie Status (sync from STB-PRODUCTIE)
Verwachte Leverdatum (date)
Montage Datum (date)
Productie Notities (multilineText)

🔗 Linked Records:
  → [BASE LINK] STB-SALES.Klantenportaal (via Opdrachtnummer)
  → [INTERNAL] Facturatie records (1:3 - drie facturen)
  → [INTERNAL] Inmeetplanning record (1:1)
  → [BASE LINK] STB-PRODUCTIE.Projecten (1:1 - na inmeet)
```

---

## 🔄 Complete Data Flow: Stap voor Stap

### FASE 1: Offorte Webhook → STB-SALES

**Trigger:** Proposal Won in Offorte

**Actions:**
```python
# Create in STB-SALES
1. Klantenportaal (1 record)
2. Elementen Overzicht (15 records)
3. Element Specificaties (15 records)
4. Subproducten (37 records)
5. Nacalculatie (15 records - empty)

# DIRECT SYNC to STB-ADMINISTRATIE
6. Projecten (1 record) ← CREATE IMMEDIATELY
7. Inmeetplanning (1 record) ← CREATE IMMEDIATELY
8. Facturatie (3 records) ← CREATE IMMEDIATELY
   - Factuur 1: 30% Vooraf (Concept)
   - Factuur 2: 65% Start (Concept)
   - Factuur 3: 5% Oplevering (Concept)
```

**Waarom direct sync?**
- Facturatie moet direct kunnen worden verstuurd (30% vooraf)
- Inmeetplanning moet direct planning kunnen maken
- Project record is centrale hub voor status tracking

---

### FASE 2: Sales Review (in STB-SALES)

**User Actions:**
```
Voor elk element in Elementen Overzicht:
1. Review Element Specificaties
2. Verify Subproducten
3. Update Status: Te Reviewen → Goedgekeurd
4. Fill Nacalculatie (kostprijs)
```

**Automation:**
```
When ALL elementen Status = Goedgekeurd:
  → Update STB-ADMINISTRATIE.Projecten.Verkoop Review Status = "Goedgekeurd"
  → Update STB-ADMINISTRATIE.Inmeetplanning.Projectstatus = "Planning Vereist"
```

---

### FASE 3: Facturatie (in STB-ADMINISTRATIE)

**User Actions:**
```
1. Open Facturatie tabel
2. Find 3 facturen for Opdrachtnummer
3. Verstuur Factuur 1 (30% Vooraf)
   - Update Status: Concept → Verzonden
   - Set Verstuurd op: [datum]
   - Set Vervaldatum: +14 dagen
```

**Factuur Berekening:**
```python
totaal_incl_btw = proposal['total_incl_btw']  # €55,138

factuur_1_bedrag = totaal_incl_btw * 0.30  # €16,541.40
factuur_2_bedrag = totaal_incl_btw * 0.65  # €35,840.00
factuur_3_bedrag = totaal_incl_btw * 0.05  # €2,756.90
```

---

### FASE 4: Inmeet Planning (in STB-ADMINISTRATIE)

**User Actions:**
```
1. Open Inmeetplanning tabel
2. Find record for Opdrachtnummer
3. Set Inmeetdatum
4. Set Toegewezen Inmeter (Jeroen/Donny)
5. Update Projectstatus: Planning Vereist → Ingepland
6. Check Start Inmeetplanning Trigger
```

**Automation:**
```
When Inmeetdatum IS SET:
  → Send notification to Inmeter
  → Update STB-ADMINISTRATIE.Projecten.Project Status = "Inmeet Planning"
  → Add to Calendar
```

---

### FASE 5: Inmeet Uitvoeren

**User Actions:**
```
1. Inmeter voert inmeet uit
2. Update Inmeetplanning:
   - Projectstatus: Ingepland → Voltooid
   - Inmeet Notities: [bevindingen]
3. Update Projecten:
   - Inmeet Voltooid: ✓
   - Project Status: Inmeet Planning → Inmeet Voltooid
```

---

### FASE 6: Sync naar Productie (in STB-ADMINISTRATIE → STB-PRODUCTIE)

**Trigger:** Projecten.Inmeet Voltooid = TRUE

**Automation Actions:**
```python
# CREATE in STB-PRODUCTIE
1. Projecten (1 record) - synced from STB-ADMINISTRATIE
2. For each element in STB-SALES.Elementen Overzicht:
   If Element Type = "Deur":
     → Create STB-PRODUCTIE.Deur Elementen (with specs)
   Else:
     → Create STB-PRODUCTIE.Kozijn Elementen (with specs)

# UPDATE in STB-ADMINISTRATIE
Projecten.Project Status = "In Productie"
Projecten.Productie Status = [sync from STB-PRODUCTIE]
```

---

## 📊 Data Transformatie: STB-SALES → STB-ADMINISTRATIE

### Klantenportaal → Projecten

```python
{
  "Project ID": auto,
  "Opdrachtnummer": klantenportaal['Opdrachtnummer'],
  "Klantnaam": klantenportaal['Klantnaam'],
  "Project Status": "Nieuw",

  "Volledig Adres": klantenportaal['Adres'],
  # Parse adres naar postcode/stad
  "Postcode": extract_postcode(adres),
  "Stad": extract_city(adres),
  "Telefoon": klantenportaal['Telefoon'],
  "Email": klantenportaal['E-mail'],

  "Totaal Verkoopprijs Excl BTW": klantenportaal['Totaalprijs Excl BTW'],
  "Totaal Verkoopprijs Incl BTW": klantenportaal['Totaalprijs Incl BTW'],
  "Aantal Elementen": count(elementen_overzicht),
  "Elementen Samenvatting": klantenportaal['Offerte Elementen Overzicht'],

  "Verkoop Review Status": "In Review",
}
```

### Klantenportaal → Inmeetplanning

```python
{
  "Opdrachtnummer": klantenportaal['Opdrachtnummer'],
  "Klant & Stad": f"{klantnaam} {stad}",
  "Telefoon": klantenportaal['Telefoon'],

  "Elementen": count(elementen_overzicht),
  "Waarde": klantenportaal['Totaalprijs Incl BTW'],
  "Projectstatus": "Planning Vereist",

  "Klantnaam": klantenportaal['Klantnaam'],
  "E-mail": klantenportaal['E-mail'],
  "Volledig Adres": klantenportaal['Adres'],
  "Stad": extract_city(adres),
  "Postcode": extract_postcode(adres),
  # Provincie: compute from postcode

  "Total Amount Incl BTW": klantenportaal['Totaalprijs Incl BTW'],
  "Aantal Elementen": count(elementen_overzicht),

  "Elementen Overzicht": format_elements_summary(elementen_overzicht),
  # "Locaties": extract from element descriptions
  # "Geschatte Uren": compute based on element count/type

  "Opdracht verkocht op": offorte_proposal['date_won'],
}
```

### Klantenportaal → Facturatie (3 records)

```python
totaal = klantenportaal['Totaalprijs Incl BTW']

# Factuur 1: 30% Vooraf
{
  "Factuur ID": f"{opdrachtnummer}-F1",
  "Opdrachtnummer": opdrachtnummer,
  "Type Factuur": "30% Vooraf",
  "Bedrag": totaal * 0.30,
  "Status": "Concept",
  "Klant": klantnaam,
  "Email": email,
  "Telefoon": telefoon,
  "Adres": adres,
  "Factuurtitel": f"Voorschotfactuur 30% - {opdrachtnummer}"
}

# Factuur 2: 65% Start
{
  "Factuur ID": f"{opdrachtnummer}-F2",
  "Type Factuur": "65% Start",
  "Bedrag": totaal * 0.65,
  "Factuurtitel": f"Factuur bij start productie 65% - {opdrachtnummer}"
}

# Factuur 3: 5% Oplevering
{
  "Factuur ID": f"{opdrachtnummer}-F3",
  "Type Factuur": "5% Oplevering",
  "Bedrag": totaal * 0.05,
  "Factuurtitel": f"Eindfactuur oplevering 5% - {opdrachtnummer}"
}
```

---

## 📊 Data Transformatie: STB-ADMINISTRATIE → STB-PRODUCTIE

### Projecten → STB-PRODUCTIE.Projecten

```python
{
  "Opdrachtnummer": projecten['Opdrachtnummer'],
  "Klant Naam": projecten['Klantnaam'],

  "Adres": projecten['Volledig Adres'],
  "Postcode": projecten['Postcode'],
  "Plaats": projecten['Stad'],

  "Projectstatus": "Nog in te meten",  # default start
  # Later: "Inmeten gepland", "Inmeten voltooid"

  "Toegewezen Inmeter": projecten['Toegewezen Inmeter'],
  "Inmeetdatum": projecten['Inmeetdatum'],

  "Telefoon": projecten['Telefoon'],
  "Email": projecten['Email'],

  "Verkocht op": lookup from inmeetplanning,
  "Opmerkingen Project": projecten['Inmeet Notities'],
}
```

### Elementen Overzicht + Specs → STB-PRODUCTIE.Deur/Kozijn Elementen

```python
# For each element in Elementen Overzicht where Status = "Goedgekeurd"

if element['Hoofdproduct Type'] in ['Deur', 'Voordeur', 'Tuindeur']:
  target_table = "STB-PRODUCTIE.Deur Elementen"
else:
  target_table = "STB-PRODUCTIE.Kozijn Elementen"

# Get linked specs
specs = element_specificaties[element['Element ID']]

{
  "Opdrachtnummer": element['Opdrachtnummer'],
  "Element ID (Merk)": element['Element ID'],

  "Soort Element": element['Hoofdproduct Type'],
  "Plaats": specs.get('Locatie', ''),

  "Oorspronkelijke Breedte": specs.get('Breedte (mm)'),
  "Oorspronkelijke Hoogte": specs.get('Hoogte (mm)'),

  "Verkoop Specificaties": element['Hoofdproduct Beschrijving'],
  "Sales Review Notities": element['Verkoop Notities'],

  # Deur specifiek (if applicable)
  "Model Deur": specs.get('Model Deur'),
  "Draairichting": specs.get('Draairichting'),
  "Type Kozijn": specs.get('Type Profiel/Kozijn'),
  "Glas Deurvleugel": specs.get('Glas Type'),
  "Kleur binnen/buiten": f"{specs.get('Kleur Binnen')} / {specs.get('Kleur Buiten')}",

  "Definitieve Element Prijs": element['Element Totaal Incl BTW'],

  "Inmeet Status": "Te inmeten",  # default
}
```

---

## 🔗 Base Links Configuration

### In Airtable Settings:

**STB-SALES ↔ STB-ADMINISTRATIE**
```
Link Field: Opdrachtnummer (beide bases)
Direction: Bi-directional
Auto-sync: Yes (on creation)

STB-SALES.Klantenportaal.Opdrachtnummer
  ↔ STB-ADMINISTRATIE.Projecten.Opdrachtnummer
```

**STB-ADMINISTRATIE ↔ STB-PRODUCTIE**
```
Link Field: Opdrachtnummer
Direction: Bi-directional
Auto-sync: On trigger (Inmeet Voltooid = TRUE)

STB-ADMINISTRATIE.Projecten.Opdrachtnummer
  ↔ STB-PRODUCTIE.Projecten.Opdrachtnummer
```

---

## 🎯 Status Flow Diagram

```
OFFORTE WEBHOOK
       ↓
┌──────────────────┐
│   STB-SALES      │
│  Status: Nieuw   │ ← Sales review elementen
└────────┬─────────┘
         │ (direct sync)
         ↓
┌──────────────────┐
│ STB-ADMINISTRATIE│
│ Status: Facturatie│ ← Verstuur 30% factuur
└────────┬─────────┘
         │ (na factuur betaald)
         ↓
┌──────────────────┐
│ STB-ADMINISTRATIE│
│Status: Inmeet Plan│ ← Plan inmeet
└────────┬─────────┘
         │ (na inmeet voltooid)
         ↓
┌──────────────────┐
│  STB-PRODUCTIE   │
│Status: Productie │ ← Maak elementen
└──────────────────┘
```

---

## ✅ Implementatie Checklist

### Fase 1: STB-SALES (We zijn hier) ✓
- [x] Offorte API werkend
- [x] Data structuur geanalyseerd
- [x] Tabel design compleet
- [ ] Sync agent implementeren

### Fase 2: STB-ADMINISTRATIE Sync
- [ ] Projecten tabel aanmaken
- [ ] Facturatie auto-create (3 facturen)
- [ ] Inmeetplanning auto-create
- [ ] Base link STB-SALES ↔ STB-ADMINISTRATIE

### Fase 3: STB-PRODUCTIE Sync (Later)
- [ ] Trigger: Inmeet Voltooid
- [ ] Sync Projecten
- [ ] Sync Elementen naar Deur/Kozijn tabellen
- [ ] Base link STB-ADMINISTRATIE ↔ STB-PRODUCTIE

---

## ❓ Beslissingen

1. **Direct sync akkoord?**
   - Offorte Won → STB-SALES + STB-ADMINISTRATIE (Projecten, Facturatie, Inmeetplanning)

2. **Facturatie auto-create?**
   - Alle 3 facturen als "Concept" status

3. **Project status triggers?**
   - Welke status changes triggeren sync?
   - Notificaties naar wie?

4. **Productie sync timing?**
   - Direct na "Inmeet Voltooid" checkbox?
   - Of wachten op andere trigger?

