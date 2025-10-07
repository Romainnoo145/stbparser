# Offorte API Data Structure - Bevindingen

**Datum:** 2025-10-07
**Geanalyseerd:** 10 grootste gewonnen proposals (€45,521 - €16,028)

## API Authenticatie

✅ **Methode:** API key als query parameter
✅ **Format:** `?api_key=YOUR_KEY`
✅ **Account:** `stb-kozijnen`
✅ **Base URL:** `https://connect.offorte.com/api/v2/stb-kozijnen`

### Endpoints

- Lijst proposals: `/proposals/won/`
- Proposal details: `/proposals/{id}/details`

## Data Structuur

### Proposal Object (Top Level)

```json
{
  "id": 288976,
  "name": "2025111L Drusedau Hout-Blerick",
  "proposal_nr": "2465",
  "status": "won",
  "date_won": "2025-05-30T14:12:23.000000Z",
  "date_created": "2025-05-21T10:08:54.000000Z",
  "price_total": "€45,521.00",
  "price_total_original": "45521.00",
  "contact": { ... },
  "content": { "pricetables": [ ... ] }
}
```

### Contact Object

```json
{
  "id": 240191,
  "type": "person",  // of "organisation"
  "name": "Drusedau",
  "fullname": "Drusedau",
  "email": "c.drusedau@outlook.com",
  "mobile": "06-14114106",
  "phone": "",
  "street": "Horatiuslaan 12",
  "zipcode": "5926 SH",
  "city": "Hout-Blerick"
}
```

### Content → Pricetables Structure

**Belangrijke bevinding:** Offorte heeft GEEN gestructureerde "elementen" met codes zoals D1, D2, etc.

In plaats daarvan:
- **Multiple pricetables** per proposal (vaak 2-5 tabellen)
- Elke pricetable bevat **rows** (regelitems)
- Elke row is een **product/dienst** met:
  - HTML `content` (beschrijving met opties)
  - `price` (prijs per stuk)
  - `quantity` (aantal)
  - `subtotal` (prijs × aantal)
  - Optioneel: `product_id`, `sku`

### Pricetable Row Voorbeeld

```json
{
  "id": "tr64153722e130a",
  "type": "price",
  "content": "<p>Schuifpui 4-delig</p>\n\n<p><em>• Inclusief HST85 GU thermostep dorpel</em></p>\n\n<p><em>• Inclusief hardstenen onderdorpel</em></p>\n\n<p><em>• Inclusief hang- & sluitwerk</em></p>\n\n<p><em>• Inclusief veiligheidsglas</em></p>\n\n<p><em>• Inclusief gelijksluitende cilinders</em></p>\n\n<p><em>• Inclusief triple glas</em></p>",
  "price": 8513,
  "quantity": 1,
  "subtotal": 8513,
  "discount_type": false,
  "discount_value": "",
  "user_selected": true,
  "product_id": null,
  "sku": ""
}
```

## Analyse Resultaten (10 proposals)

- **Total analyzed:** 10 proposals
- **Total rows:** 285 regelitems
- **Row types:** Alleen "price" type
- **Gemiddeld:** ~28 regelitems per proposal

### Row Content Patterns

De `content` field bevat HTML met:
- Hoofdproduct naam (bijv. "Schuifpui 4-delig", "Draaikiep raam", "Vast raam")
- Bulleted list met specificaties:
  - Triple glas
  - Kleur/afwerking (bijv. "antraciet houtnerf structuur")
  - Hang & sluitwerk
  - Dorpel type
  - Veiligheidsglas
  - Gelijksluitende cilinders
  - Ventilatie
  - Kranen/vacuümzuigers

**Voorbeelden van producten:**
- Vast raam
- Draaikiep raam
- Schuifpui 2/3/4-delig
- Dubbele tuindeur
- Ventilatierooster
- Klemhor
- Afsluitbare kruk
- Plisse hordeur

## Implicaties voor Airtable Sync

### ❌ Oorspronkelijke Aanname (INCORRECT)

We gingen ervan uit dat Offorte gestructureerde bouwkundige elementen heeft met:
- Element codes (D1, D2, K1, etc.)
- Gekoppelde varianten
- Gestructureerde specificaties per veld

### ✅ Werkelijke Situatie

Offorte gebruikt een **flexibel pricetable systeem**:
- Geen vaste element structuur
- HTML-gebaseerde beschrijvingen
- Vrije-vorm specificaties
- Geen element groepering (behalve via pricetables)

### 🔄 Aanpassingen Nodig

1. **Elementen Review tabel:**
   - Parsen van HTML content naar gestructureerde velden
   - Element type detectie via regex (zoek naar "deur", "raam", "schuifpui", etc.)
   - Specificaties extraheren uit bullet points

2. **Deur Specificaties tabel:**
   - Alleen vullen voor rows die deur-gerelateerd zijn
   - HTML parsing voor:
     - Glas type (triple/HR++/etc.)
     - Kleur (antraciet/etc.)
     - Dorpel type
     - Beslag/hang&sluitwerk

3. **Geen coupled elements:**
   - Element_groep_id is niet relevant
   - Geen D1/D2 varianten in Offorte data
   - Simpeler: elk row = 1 element

4. **Inmeetplanning:**
   - Kan gevuld worden met contact info + proposal totals
   - Aantal elementen = aantal rows in pricetables

## Volgende Stappen

1. ✅ Update `backend/core/settings.py` - API key as query param
2. ✅ Update `.env` - OFFORTE_ACCOUNT_NAME=stb-kozijnen
3. 🔄 Herschrijf `parse_construction_elements()` in tools.py
4. 🔄 Herschrijf alle `_transform_*()` functies
5. 🔄 Simpeler mapping: pricetable rows → Airtable records
6. ✅ Test met echte Offorte data

## HTML Parsing Strategie

Voor het extraheren van specificaties uit HTML content:

```python
from bs4 import BeautifulSoup
import re

def parse_element_from_row(row):
    html_content = row['content']
    soup = BeautifulSoup(html_content, 'html.parser')

    # Hoofdproduct = eerste <p> tag
    main_product = soup.find('p').get_text(strip=True)

    # Specificaties = alle <li> items
    specs = [li.get_text(strip=True) for li in soup.find_all('li')]

    # Element type detectie
    element_type = detect_element_type(main_product)

    return {
        'element_type': element_type,
        'hoofdproduct': main_product,
        'specificaties': specs,
        'prijs': row['price'],
        'aantal': row['quantity']
    }
```

## Voorbeeld Transformatie

**Offorte Row:**
```json
{
  "content": "<p>Draaikiep raam</p><ul><li>Inclusief triple glas</li><li>Inclusief complete buitenzijde antraciet houtnerf structuur</li></ul>",
  "price": 1080,
  "quantity": 1
}
```

**→ Airtable Elementen Review:**
```json
{
  "Opdrachtnummer": "2465",
  "Element Type": "Raam",
  "Hoofdproduct": "Draaikiep raam",
  "Alle Regelitems Detail": "• Inclusief triple glas\n• Inclusief complete buitenzijde antraciet houtnerf structuur",
  "Hoofdproduct Prijs": 1080,
  "Aantal": 1,
  "Element Totaal": 1080
}
```

