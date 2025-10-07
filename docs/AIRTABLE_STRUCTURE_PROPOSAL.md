# Airtable Structuur Voorstel - STB-SALES Base

## 🎯 Doel

**Maximale data overdracht** van Offorte → Airtable met minimale data loss en flexibiliteit voor variaties.

## 📋 Huidige vs Voorgestelde Structuur

### Tabel 1: Klantenportaal (BEHOUDEN)

**Doel:** Overzicht van gewonnen offertes per klant

**Velden: 10** (geen wijzigingen nodig)
```
✅ Opdrachtnummer (key field)
✅ Klantnaam
✅ Adres (multilineText)
✅ Telefoon
✅ E-mail
✅ Totaalprijs Excl BTW (currency)
✅ Totaalprijs Incl BTW (currency)
✅ Offerte Elementen Overzicht (multilineText)
✅ Verkoop Notities (multilineText)
✅ Aangemaakt op (createdTime)
```

**Offorte Data:**
```python
{
  "Opdrachtnummer": proposal['proposal_nr'],
  "Klantnaam": contact['fullname'],
  "Adres": f"{contact['street']}\n{contact['zipcode']} {contact['city']}",
  "Telefoon": contact['mobile'] or contact['phone'],
  "E-mail": contact['email'],
  "Totaalprijs Excl BTW": price_total_original,
  "Totaalprijs Incl BTW": sum(table['total'] for table in pricetables),
  "Offerte Elementen Overzicht": generate_summary(pricetables),
  "Verkoop Notities": ""  # Handmatig
}
```

---

### Tabel 2: Elementen Review (HERZIEN)

**Doel:** Elk element (=pricetable) met hoofdproduct + alle opties/subproducten

#### ❌ Probleem Huidige Structuur

- **61 velden** is te veel en inflexibel
- **Regelitems 1-10 hardcoded** → wat als er 15 opties zijn?
- **30 velden voor regelitems** (10 x 3 = naam/groep/prijs) → niet schaalbaar

#### ✅ Voorgestelde Structuur: 25 Velden

**Core Identificatie (5)**
```
Opdrachtnummer (singleLineText) [KEY]
Element ID (singleLineText) - formaat: "{opdracht}-E{index}"
Element Volgnummer (number) - pricetable index
Klantnaam (singleLineText)
```

**Hoofdproduct Info (6)**
```
Hoofdproduct Type (singleSelect) - Deur/Raam/Schuifpui/Accessoire/Anders
Hoofdproduct Naam (singleLineText) - "Schuifpui 4-delig"
Hoofdproduct Beschrijving (multilineText) - HTML parsed, alle specs
Hoofdproduct Prijs Excl BTW (currency) - eerste row prijs
Hoofdproduct Aantal (number) - eerste row quantity
```

**Subproducten/Opties (4)**
```
🔧 NIEUW: Subproducten Count (number) - aantal optie rows
🔧 NIEUW: Subproducten Detail (multilineText) - per regel: "Meerprijs kleur | €245 | 1x"
🔧 NIEUW: Subproducten Totaal (currency) - som van alle optie rows
Alle Regelitems Detail (multilineText) - BACKUP: alle rows raw HTML
```

**Prijzen & Totalen (6)**
```
Element Subtotaal Excl BTW (currency) - pricetable.subtotal
Element Korting (currency) - berekend of 0
Element Totaal Excl BTW (currency) - na korting
Element BTW Bedrag (currency) - pricetable.vat[0].total
Element BTW Percentage (number) - 21
Element Totaal Incl BTW (currency) - pricetable.total
```

**Review & Nacalculatie (4)**
```
Verkoop Review Status (singleSelect) - Te Reviewen/Goedgekeurd/Afgekeurd
Review Notities (multilineText)
🔧 NIEUW: Nacalculatie Kostprijs (currency) - handmatig
🔧 NIEUW: Nacalculatie Marge (formula) - (Element Totaal - Kostprijs) / Element Totaal * 100
```

**Totaal: 25 velden** (vs 61 huidig)

---

### Tabel 3: Deur Specificaties (OPTIONEEL - ALLEEN VOOR DEUREN)

**Vraag:** Willen we dit nog?

**Optie A: BEHOUDEN maar simplificeren**
- Alleen vullen voor elements waar `Hoofdproduct Type = "Deur"`
- Parse HTML specs naar specifieke velden (kleur, glas, etc.)
- **Probleem:** HTML parsing is niet 100% betrouwbaar

**Optie B: VERWIJDEREN**
- Alle specs zitten al in Elementen Review → Hoofdproduct Beschrijving
- Verkoper kan handmatig aanvullen in review proces
- **Voordeel:** Simpeler, minder data loss risk

**Optie C: HERNOEMEN naar "Element Specificaties"**
- Voor ALLE element types (niet alleen deuren)
- Meer generieke velden:
  ```
  Opdrachtnummer [key]
  Element ID Ref [link naar Elementen Review]

  Specificatie Type (singleSelect) - Glas/Kleur/Beslag/Afwerking/Anders
  Specificatie Naam (singleLineText) - "Triple glas"
  Specificatie Waarde (singleLineText) - "HR+++ isolatieglas"
  Specificatie Bron (singleSelect) - Hoofdproduct/Subproduct
  ```
- **Voordeel:** Flexibel voor alle element types
- **Nadeel:** Veel meer records (1 spec = 1 record)

**🔸 Mijn Aanbeveling: Optie B (verwijderen)**
- Alle specs zitten in Elementen Review
- Verkoper kan in Airtable interface aanvullen wat nodig is
- Geen risico op parsing errors

---

## 📊 Voorbeeld Data Flow

### Offorte Proposal 288976 (€45,521)

**15 Pricetables →** 15 Records in Elementen Review

#### Pricetable 1 → Element Record 1
```json
{
  "Opdrachtnummer": "2465",
  "Element ID": "2465-E1",
  "Element Volgnummer": 1,
  "Klantnaam": "Drusedau",

  "Hoofdproduct Type": "Raam",
  "Hoofdproduct Naam": "Vast raam",
  "Hoofdproduct Beschrijving": "• Inclusief triple glas\n• Inclusief kraan met vacuümzuigers\n• Inclusief complete buitenzijde antraciet houtnerf structuur",
  "Hoofdproduct Prijs Excl BTW": 1645.00,
  "Hoofdproduct Aantal": 2,

  "Subproducten Count": 1,
  "Subproducten Detail": "Ventilatierooster | €202 | 2x",
  "Subproducten Totaal": 404.00,
  "Alle Regelitems Detail": "[RAW HTML BACKUP]",

  "Element Subtotaal Excl BTW": 3694.00,
  "Element Korting": 0.00,
  "Element Totaal Excl BTW": 3694.00,
  "Element BTW Bedrag": 775.74,
  "Element BTW Percentage": 21,
  "Element Totaal Incl BTW": 4469.74,

  "Verkoop Review Status": "Te Reviewen",
  "Review Notities": "",
  "Nacalculatie Kostprijs": null,
  "Nacalculatie Marge": null
}
```

#### Pricetable 2 → Element Record 2
```json
{
  "Opdrachtnummer": "2465",
  "Element ID": "2465-E2",
  "Element Volgnummer": 2,

  "Hoofdproduct Type": "Schuifpui",
  "Hoofdproduct Naam": "Schuifpui 4-delig",
  "Hoofdproduct Beschrijving": "• Inclusief HST85 GU thermostep dorpel\n• Inclusief hardstenen onderdorpel\n• Inclusief hang- & sluitwerk\n• Inclusief veiligheidsglas\n• Inclusief gelijksluitende cilinders\n• Inclusief triple glas\n• Inclusief kraan met vacuümzuigers\n• Inclusief complete buitenzijde antraciet houtnerf structuur",
  "Hoofdproduct Prijs Excl BTW": 8513.00,
  "Hoofdproduct Aantal": 1,

  "Subproducten Count": 2,
  "Subproducten Detail": "Afsluitbare kruk buitenzijde (zwart of RVS) | €185 | 2x\nDubbele plisse hordeur | €685 | 1x",
  "Subproducten Totaal": 1055.00,

  "Element Subtotaal Excl BTW": 9198.00,
  "Element Totaal Incl BTW": 11129.58,
  ...
}
```

---

## 🎨 Veldtype Keuzes

### Waarom multilineText voor Beschrijvingen?

**Voordeel:**
- Behoudt alle data (geen loss)
- Flexibel voor variaties
- Verkoper kan lezen en interpreteren
- Geen parsing errors

**Nadeel:**
- Niet queryable per spec
- Handmatige review nodig

**Alternatief:** Gestructureerde JSON in longText?
```json
{
  "specs": [
    {"type": "glas", "value": "Triple glas"},
    {"type": "kleur", "value": "Antraciet houtnerf"},
    {"type": "dorpel", "value": "Hardstenen onderdorpel"}
  ]
}
```
**Probleem:** Airtable JSON support is beperkt

---

## ✅ Implementatie Voordelen

### 1. Schaalbaar
- Geen limiet op aantal opties (niet 1-10 hardcoded)
- Werkt voor alle proposal groottes (1-15+ tables)

### 2. Data Behoud
- Alle HTML in "Alle Regelitems Detail" backup
- Parsed data in gestructureerde velden
- Geen data loss

### 3. Flexibel
- Verkoper kan handmatig aanvullen
- Review workflow built-in
- Nacalculatie velden voor kostprijsanalyse

### 4. Simpel
- 1 pricetable = 1 record (duidelijk)
- Geen complexe parsing logica
- Minder velden (25 vs 61)

---

## ❓ Vragen voor Beslissing

1. **Deur Specificaties tabel:**
   - ⬜ Behouden en vullen (effort: hoog, risico: parsing errors)
   - ⬜ Behouden maar leeg laten (verkoper vult handmatig)
   - ✅ **Verwijderen** (alles in Elementen Review) ← **AANBEVELING**

2. **Subproducten Detail formaat:**
   - ✅ **Per regel: "Naam | Prijs | Aantal"** ← **AANBEVELING**
   - ⬜ Bullet list: "• Naam (€prijs, 2x)"
   - ⬜ Table markdown format

3. **HTML Parsing niveau:**
   - ✅ **Basis: Extract bullets, clean HTML** ← **AANBEVELING**
   - ⬜ Geavanceerd: Parse specs naar aparte velden (glas_type, kleur, etc.)
   - ⬜ Geen: Raw HTML opslaan

4. **Element Type detectie:**
   - ✅ **Keyword matching met fallback "Anders"** ← **AANBEVELING**
   - ⬜ AI/LLM classificatie (meer complex)
   - ⬜ Handmatig classificeren na import

---

## 🚀 Volgende Stappen

1. **Feedback op structuur** - akkoord of wijzigingen?
2. **Beslissing Deur Specificaties tabel** - behouden/verwijderen?
3. **Airtable schema update** - ik kan helpen met field mapping
4. **Code implementatie** - sync agent herschrijven
5. **Test run** - met echte proposals

