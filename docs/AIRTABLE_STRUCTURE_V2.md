# Airtable Structuur V2 - Vindbaarheid & Bruikbaarheid

## 🎯 Kernprobleem

**Jouw punt:** Deurspecificaties heeft aparte tabel omdat:
- Andere velden nodig (glas type, kleur kozijn, beslag, cilinder, etc.)
- Moet **doorzoekbaar** zijn (filter op "alle deuren met triple glas")
- Moet **bruikbaar** zijn voor nacalculatie/productie
- Multiline text is **niet queryable** in Airtable

## 💡 Herziene Oplossing: 3-Tabel Structuur

### Tabel 1: Klantenportaal (ONGEWIJZIGD)
Overzicht gewonnen offertes

### Tabel 2: Elementen Overzicht (NIEUW NAAM)
**Doel:** High-level overzicht per element

**25 velden:**
```
# Identificatie
- Opdrachtnummer [key]
- Element ID (2465-E1)
- Element Volgnummer (1, 2, 3...)
- Klantnaam

# Hoofdproduct
- Hoofdproduct Type (Deur/Raam/Schuifpui/Accessoire)
- Hoofdproduct Naam ("Schuifpui 4-delig")
- Hoofdproduct Beschrijving (parsed bullets)
- Hoofdproduct Prijs
- Hoofdproduct Aantal

# Subproducten
- Subproducten Count
- Subproducten Detail (backup text)
- Subproducten Totaal

# Prijzen
- Element Subtotaal Excl BTW
- Element Korting
- Element Totaal Excl BTW
- Element BTW Bedrag
- Element Totaal Incl BTW

# Review
- Verkoop Review Status
- Review Notities
- Nacalculatie Kostprijs
- Nacalculatie Marge

# Links naar detail tabellen
🔗 Link naar Deur Specificaties (multipleRecordLinks)
🔗 Link naar Subproducten (multipleRecordLinks)
```

### Tabel 3: Element Specificaties (HERNOEMEN VAN "DEUR SPECIFICATIES")

**Doel:** Doorzoekbare, gestructureerde specs per element

**Strategie:** 1 Element kan MULTIPLE spec records hebben

**30 velden:**
```
# Identificatie
- Opdrachtnummer [key]
- Element ID Ref (link naar Elementen Overzicht)
- Spec Record ID (auto-generated)
- Klantnaam

# Element Context
- Element Type (Deur/Raam/Schuifpui) [filter helper]
- Element Naam ("Schuifpui 4-delig")
- Locatie (optioneel - uit Offorte description)

# Afmetingen (PARSED of MANUAL)
- Geoffreerde Afmetingen (text zoals in Offorte)
- Breedte (mm) (number - parsed of handmatig)
- Hoogte (mm) (number - parsed of handmatig)

# GLAS SPECIFICATIES
- Glas Type (singleSelect: Triple/HR++/HR+++/Veiligheidsglas/Anders)
- Glas Detail (text)

# KLEUR/AFWERKING
- Kleur Kozijn (text)
- Kleur Binnen (text - voor deuren)
- Kleur Buiten (text - voor deuren)
- Afwerking Type (singleSelect: Houtnerf/Glad/Structuur)

# DEUR SPECIFIEK
- Model Deur (text)
- Type Profiel/Kozijn (singleSelect)
- Draairichting (singleSelect: Links/Rechts)

# BESLAG/HARDWARE
- Deurbeslag Binnen (text)
- Deurbeslag Buiten (text)
- Staafgreep Specificatie (text)
- Scharnieren Type (text)
- Type Cilinder (text)
- Cilinder Gelijksluitend (singleSelect: Ja/Nee)

# DORPEL/ONDERDELEN
- Soort Onderdorpel (text)
- Brievenbus (singleSelect: Ja/Nee)
- Afwatering (singleSelect)

# OVERIG
- Binnenafwerking (text)
- Ventilatie (text)
- Extra Opties (multilineText) - alles wat niet past

# REVIEW
- Verkoop Review Status (singleSelect)
- Opmerkingen voor Binnendienst (multilineText)
- Definitieve Element Prijs (currency - kan afwijken)
```

### Tabel 4: Subproducten (NIEUW)

**Doel:** Elke optie/toeslag als apart record voor queries

**Waarom apart?**
- Filter: "Toon alle projecten met meerprijs kleur"
- Rapportage: "Hoeveel hordeuren verkopen we gemiddeld?"
- Nacalculatie: Kostprijs per subproduct

**15 velden:**
```
# Identificatie
- Subproduct ID (auto-generated) [key]
- Opdrachtnummer
- Element ID Ref (link naar Elementen Overzicht)
- Klantnaam

# Subproduct Info
- Subproduct Type (singleSelect: Meerprijs/Extra/Optie/Accessoire)
- Subproduct Naam ("Meerprijs afwijkende kleur")
- Subproduct Beschrijving (parsed specs)
- Subproduct Categorie (singleSelect: Kleur/Glas/Beslag/Hordeur/Ventilatie/Anders)

# Prijzen
- Prijs Per Stuk Excl BTW (currency)
- Aantal (number)
- Subtotaal Excl BTW (formula: Prijs × Aantal)

# Optioneel
- Product ID (uit Offorte, indien aanwezig)
- SKU (uit Offorte, indien aanwezig)

# Nacalculatie
- Kostprijs (currency - handmatig)
- Marge (formula)
```

---

## 📊 Data Flow Voorbeeld

### Offorte Pricetable 2 (Schuifpui + opties)

**Offorte Data:**
```json
{
  "rows": [
    {
      "content": "<p>Schuifpui 4-delig</p>\n<ul>\n<li>Inclusief HST85 GU thermostep dorpel</li>\n<li>Inclusief hardstenen onderdorpel</li>\n<li>Inclusief hang- & sluitwerk</li>\n<li>Inclusief veiligheidsglas</li>\n<li>Inclusief gelijksluitende cilinders</li>\n<li>Inclusief triple glas</li>\n<li>Inclusief complete buitenzijde antraciet houtnerf structuur</li>\n</ul>",
      "price": 8513,
      "quantity": 1
    },
    {
      "content": "<p>Afsluitbare kruk buitenzijde (zwart of RVS)</p>",
      "price": 185,
      "quantity": 2
    },
    {
      "content": "<p>Dubbele plisse hordeur</p>",
      "price": 685,
      "quantity": 1
    }
  ],
  "subtotal": 9198,
  "total": 11129.58
}
```

**→ Airtable Record 1: Elementen Overzicht**
```json
{
  "Opdrachtnummer": "2465",
  "Element ID": "2465-E2",
  "Element Volgnummer": 2,
  "Hoofdproduct Type": "Schuifpui",
  "Hoofdproduct Naam": "Schuifpui 4-delig",
  "Hoofdproduct Prijs": 8513.00,
  "Subproducten Count": 2,
  "Element Totaal Excl BTW": 9198.00,
  "Element Totaal Incl BTW": 11129.58
}
```

**→ Airtable Record 2: Element Specificaties**
```json
{
  "Opdrachtnummer": "2465",
  "Element ID Ref": "2465-E2", // link
  "Element Type": "Schuifpui",
  "Element Naam": "Schuifpui 4-delig",

  // PARSED uit HTML
  "Glas Type": "Triple",
  "Kleur Buiten": "Antraciet houtnerf structuur",
  "Soort Onderdorpel": "Hardstenen onderdorpel + HST85 GU thermostep",
  "Type Cilinder": "Gelijksluitende cilinders",
  "Cilinder Gelijksluitend": "Ja",

  // Extra Opties veld (voor rest)
  "Extra Opties": "• Hang- en sluitwerk met 3-puntsluiting\n• Veiligheidsglas"
}
```

**→ Airtable Records 3 & 4: Subproducten**
```json
// Record 3
{
  "Subproduct ID": "SP-2465-E2-1",
  "Opdrachtnummer": "2465",
  "Element ID Ref": "2465-E2",
  "Subproduct Type": "Optie",
  "Subproduct Naam": "Afsluitbare kruk buitenzijde",
  "Subproduct Beschrijving": "Zwart of RVS",
  "Subproduct Categorie": "Beslag",
  "Prijs Per Stuk Excl BTW": 185.00,
  "Aantal": 2,
  "Subtotaal Excl BTW": 370.00
}

// Record 4
{
  "Subproduct ID": "SP-2465-E2-2",
  "Opdrachtnummer": "2465",
  "Element ID Ref": "2465-E2",
  "Subproduct Type": "Accessoire",
  "Subproduct Naam": "Dubbele plisse hordeur",
  "Subproduct Categorie": "Hordeur",
  "Prijs Per Stuk Excl BTW": 685.00,
  "Aantal": 1,
  "Subtotaal Excl BTW": 685.00
}
```

---

## 🔍 Vindbaarheid & Gebruik Cases

### Use Case 1: Filter alle projecten met triple glas
```
Element Specificaties tabel
Filter: Glas Type = "Triple"
→ Zie alle elementen met triple glas
→ Gekoppeld aan Elementen Overzicht voor totaalprijs
```

### Use Case 2: Hoeveel hordeuren verkopen we?
```
Subproducten tabel
Filter: Subproduct Categorie = "Hordeur"
Groeperen: Per maand
→ Verkoop trend hordeuren
```

### Use Case 3: Gemiddelde meerprijs voor afwijkende kleuren
```
Subproducten tabel
Filter: Subproduct Naam contains "Meerprijs" AND "kleur"
Average: Prijs Per Stuk
→ Pricing insights
```

### Use Case 4: Nacalculatie per project
```
Elementen Overzicht
→ Linked records: Element Specificaties (specs)
→ Linked records: Subproducten (opties)
→ Formule: Totaal Verkoop - Totaal Kostprijs = Marge
```

### Use Case 5: Productie planning
```
Element Specificaties tabel
Filter: Verkoop Review Status = "Goedgekeurd"
       AND Element Type = "Deur"
       AND Glas Type = "Triple"
→ Bestel triple glas voor deze deuren
```

---

## 🎨 HTML Parsing Strategie

### Niveau 1: Keyword Matching (BETROUWBAAR)

```python
def parse_specs_from_html(content: str) -> dict:
    """Parse HTML specs naar gestructureerde velden."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text().lower()
    bullets = [li.get_text(strip=True) for li in soup.find_all('li')]

    specs = {
        'glas_type': None,
        'kleur_buiten': None,
        'dorpel_type': None,
        'cilinder': None,
        'extra_opties': []
    }

    for bullet in bullets:
        bullet_lower = bullet.lower()

        # Glas detectie
        if 'triple' in bullet_lower:
            specs['glas_type'] = 'Triple'
        elif 'hr+++' in bullet_lower:
            specs['glas_type'] = 'HR+++'
        elif 'hr++' in bullet_lower:
            specs['glas_type'] = 'HR++'
        elif 'veiligheidsglas' in bullet_lower:
            if not specs['glas_type']:  # alleen als nog niet gezet
                specs['glas_type'] = 'Veiligheidsglas'

        # Kleur detectie
        if any(k in bullet_lower for k in ['antraciet', 'kleur', 'structuur', 'afwerking']):
            specs['kleur_buiten'] = bullet

        # Dorpel detectie
        if 'dorpel' in bullet_lower:
            specs['dorpel_type'] = bullet

        # Cilinder detectie
        if 'cilinder' in bullet_lower:
            specs['cilinder'] = bullet

        # Rest gaat naar extra opties
        if not any([
            'glas' in bullet_lower,
            'kleur' in bullet_lower,
            'dorpel' in bullet_lower,
            'cilinder' in bullet_lower
        ]):
            specs['extra_opties'].append(bullet)

    return specs
```

### Niveau 2: Fallback (SAFE)

```python
# Als parsing faalt of onzeker is:
specs['extra_opties'] = '\n'.join(all_bullets)  # Bewaar alles
```

---

## ✅ Voordelen van deze Structuur

### 1. **Vindbaarheid** ✓
- Element Specificaties: Filter op glas, kleur, type
- Subproducten: Query op categorie, naam
- Gekoppeld via Element ID

### 2. **Bruikbaarheid** ✓
- Nacalculatie per element + subproducten
- Productie planning via specs
- Rapportage via filters

### 3. **Flexibiliteit** ✓
- Specs kunnen handmatig aangevuld
- Subproducten zijn uitbreidbaar
- Geen limiet op aantal

### 4. **Data Behoud** ✓
- Extra Opties veld voor unparsable specs
- Subproduct Beschrijving voor raw text
- Geen data loss

### 5. **Schaalbaarheid** ✓
- Werkt voor 1-15+ elementen per project
- Werkt voor 0-10+ subproducten per element
- Geen hardcoded limieten

---

## 📋 Import Flow per Proposal

```
1 Offorte Proposal (15 pricetables)
  ↓
CREATES:
  - 1 record in Klantenportaal
  - 15 records in Elementen Overzicht (1 per table)
  - 15 records in Element Specificaties (1 per table, parsed)
  - 37 records in Subproducten (alle optie rows)

Total: 68 Airtable records voor 1 proposal
```

---

## ❓ Beslissingen Nodig

1. **Structuur akkoord?**
   - 4 tabellen: Klantenportaal + Elementen Overzicht + Element Specificaties + Subproducten

2. **Parsing niveau?**
   - Keyword matching voor specs (glas, kleur, dorpel, cilinder)
   - Rest in "Extra Opties" veld
   - Handmatige review/aanvulling mogelijk

3. **Element Specificaties velden?**
   - Huidige 30 velden akkoord?
   - Meer/minder nodig?

4. **Subproducten categorieën?**
   - Voorgesteld: Kleur/Glas/Beslag/Hordeur/Ventilatie/Anders
   - Andere categorieën nodig?

