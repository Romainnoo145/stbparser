# Offorte Data Variaties - Gedetailleerde Analyse

**Datum:** 2025-10-07
**Geanalyseerd:** 50 gewonnen proposals van stb-kozijnen account
**Focus:** Structuurverschillen tussen gebruikers en offertes

## Gebruikers Verdeling

- **User 9867 (Jeroen Mans):** 3 proposals, gemiddeld €5,773
- **User 9985 (Luc Hoeijmakers):** 47 proposals, gemiddeld €9,974

## 🔍 Belangrijkste Bevindingen

### 1. Multiple Pricetables per Proposal

**Variatie:** Aantal tabellen varieert enorm!
- Grootste proposal (€45k): **15 pricetables**
- Gemiddelde: 5-10 tabellen per proposal
- Elk tabel = 1 bouwkundig element/locatie

**Voorbeeld:** Proposal 288976 (€45,521)
```
Table 1: 2 rows - €3,694 (Vast raam x2)
Table 2: 3 rows - €9,198 (Schuifpui 4-delig + opties)
Table 3: 2 rows - €1,080 (Draaikiep raam)
Table 4: 2 rows - €1,080 (Draaikiep raam)
...
Table 15: 1 row - €85 (Accessoire)
```

**Implicatie:** Elk pricetable = potentieel apart element in Airtable!

### 2. Opties/Toeslagen Structuur

#### Pattern A: Opties als Separate Rows (MEEST VOORKOMEND)

```json
{
  "rows": [
    {
      "content": "<p>Voordeur met vast zijlicht</p>...",
      "price": 3451,
      "quantity": 1
    },
    {
      "content": "<p>Meerprijs afwijkende kleur / structuur buitenzijde</p>...",
      "price": 245,
      "quantity": 1
    },
    {
      "content": "<p><strong>Meerprijs luxe paneeldeur</strong></p>...",
      "price": 450,
      "quantity": 1
    }
  ]
}
```

**Kenmerken:**
- Hoofdproduct in eerste row
- Meerprijs/opties als aparte rows
- Keywords: "Meerprijs", "Toeslag", "Extra"
- Elk heeft eigen price + quantity

**Voorkomen:** 22 van 177 rows (12%)

#### Pattern B: Opties in Beschrijving (STANDAARD)

```json
{
  "content": "<p>Draaikiep raam</p>
             <ul>
               <li>Inclusief triple glas</li>
               <li>Inclusief complete buitenzijde antraciet houtnerf structuur</li>
             </ul>",
  "price": 1080,
  "quantity": 1
}
```

**Kenmerken:**
- Alle opties in HTML bullets
- Keyword: "Inclusief"
- Één totaalprijs

**Voorkomen:** ~70% van alle rows

### 3. Korting Patronen

#### Pattern 1: Korting in Row (ZELDZAAM)

```json
{
  "content": "<p>Schuifpui 3-delig</p>...",
  "price": 5569,
  "discount_type": true,
  "discount_value": "400",
  "subtotal": 5169
}
```

**Voorkomen:** Slechts 2 van 177 rows hadden discount_value

#### Pattern 2: Korting als Text in Content (SOMS)

```json
{
  "content": "<p>Dubbele tuindeuren...</p>
             <p><em><span style=\"color:#be123c\">
             *Korting €484,- korting inclusief btw*
             </span></em></p>",
  "price": 5569
}
```

#### Pattern 3: Geen Expliciete Korting (MEEST)

Korting is al verwerkt in de prijs, niet zichtbaar.

### 4. Product ID Usage

- **Met product_id:** 2 van 177 rows (<2%)
- **Zonder product_id:** 98% van alle rows

**Conclusie:** product_id is niet betrouwbaar voor identificatie

### 5. HTML Content Patterns

**Analyse van 177 rows:**

| Pattern | Count | Percentage |
|---------|-------|------------|
| Mentions glass (triple/HR++) | 55 | 31% |
| Mentions color | 54 | 30% |
| Has "inclusief" | 30 | 17% |
| Has bullet list | 25 | 14% |
| Separate option row | 22 | 12% |

**Bullet Count Variatie:**
- 1 bullet: 6 rows
- 2 bullets: 6 rows
- 3 bullets: 4 rows
- 4 bullets: 6 rows
- 6 bullets: 3 rows

### 6. Hoofdproduct Detectie

**Meest voorkomende types** (eerste <p> tag):
- "Vast raam"
- "Draaikiep raam"
- "Schuifpui [2/3/4]-delig"
- "Voordeur met [vast/draai] zijlicht"
- "Dubbele tuindeur"
- "Dubbele openslaande deur"

**Opties/toeslagen types:**
- "Meerprijs afwijkende kleur"
- "Meerprijs luxe paneeldeur"
- "Triple glas" (als aparte row)
- "HR+++ glas"
- "Ventilatierooster"
- "Klemhor"
- "Afsluitbare kruk"
- "Plisse hordeur"

### 7. Specificaties Patronen

#### Glas Types
- "Triple glas" (meest voorkomend)
- "HR++ glas"
- "HR+++ glas"
- "Veiligheidsglas"

#### Kleuren/Afwerking
- "Antraciet houtnerf structuur"
- "Staalblauw AP41"
- "Complete buitenzijde [kleur]"
- "Afwijkende kleur / structuur"

#### Hardware/Beslag
- "Hang- en sluitwerk met 3-puntsluiting"
- "Gelijksluitende cilinders"
- "Staafgreep RVS P45, 30x600 mm"
- "Afsluitbare kruk (zwart of RVS)"

#### Dorpels
- "Hardstenen onderdorpel"
- "HST85 GU thermostep dorpel"

## 🚨 Kritieke Uitdagingen voor Parsing

### Uitdaging 1: Hoofdproduct vs Optie Onderscheid

**Probleem:** Hoe weet je of een row een hoofdproduct is of een optie?

**Mogelijke Oplossingen:**
1. **Eerste row in table = hoofdproduct** (85% betrouwbaar)
2. **Keyword detectie:** "Meerprijs", "Extra", "Toeslag" = optie
3. **Price threshold:** Rows < €500 zijn vaak opties
4. **Manual review:** Custom field in Airtable voor verificatie

### Uitdaging 2: Element Groepering

**Probleem:** Hoe group je opties bij het juiste hoofdproduct?

**Oplossing:** Gebruik pricetable als groep!
- Elk pricetable = 1 element met opties
- Table index = element volgnummer
- Alle rows in dezelfde table horen bij elkaar

### Uitdaging 3: Specificaties Extractie

**Probleem:** HTML bullet lists hebben geen vaste structuur

**Strategie:**
```python
def extract_specs(content):
    soup = BeautifulSoup(content, 'html.parser')

    # Hoofdproduct = eerste <p>
    main = soup.find('p')
    main_text = main.get_text(strip=True) if main else ""

    # Specs = alle <li> items
    specs = [li.get_text(strip=True) for li in soup.find_all('li')]

    # Categoriseer specs
    glass_type = next((s for s in specs if 'glas' in s.lower()), None)
    color = next((s for s in specs if any(c in s.lower() for c in ['kleur', 'antraciet', 'structuur'])), None)

    return {
        'main_product': main_text,
        'glass_type': glass_type,
        'color': color,
        'all_specs': '\n'.join(specs)
    }
```

### Uitdaging 4: Prijs Aggregatie

**Probleem:** Hoe bereken je de totale prijs van een element met opties?

**Oplossing:** Gebruik pricetable.subtotal!
- Elk pricetable heeft een `subtotal` field
- Dit is de som van alle rows in dat table
- Inclusief kortingen en meerprijzen

## 📊 Transformatie Strategie

### Nieuwe Mapping: Pricetable → Airtable Element

```python
for table_idx, pricetable in enumerate(proposal['content']['pricetables']):
    # Bepaal hoofdproduct (eerste row in table)
    main_row = pricetable['rows'][0]

    # Verzamel alle opties (overige rows)
    option_rows = pricetable['rows'][1:]

    # Parse hoofdproduct
    main_specs = extract_specs(main_row['content'])

    # Creëer Airtable record
    element_record = {
        'Opdrachtnummer': proposal['proposal_nr'],
        'Element ID Ref': f"{proposal['proposal_nr']}-E{table_idx+1}",
        'Element Type': detect_element_type(main_specs['main_product']),
        'Hoofdproduct': main_specs['main_product'],
        'Hoofdproduct Prijs': main_row['price'],
        'Totaal Regelitems': len(pricetable['rows']),
        'Alle Regelitems Detail': format_all_rows(pricetable['rows']),
        'Element Subtotaal': pricetable['subtotal'],
        'Element Totaal': pricetable['total'],
        'Element BTW': pricetable['vat'][0]['total']
    }
```

### Element Type Detectie

```python
def detect_element_type(product_text):
    text_lower = product_text.lower()

    if any(k in text_lower for k in ['deur', 'voordeur', 'tuindeur', 'openslaand']):
        return 'Deur'
    elif any(k in text_lower for k in ['schuifpui', 'schuifdeur', 'hst']):
        return 'Schuifpui'
    elif any(k in text_lower for k in ['raam', 'draaikiep', 'vast raam']):
        return 'Raam'
    elif any(k in text_lower for k in ['hordeur', 'ventilatie', 'rooster']):
        return 'Accessoire'
    else:
        return 'Anders'
```

## ✅ Aanbevelingen

1. **Gebruik pricetable als primaire groepering**
   - Elk table = 1 element in Elementen Review
   - Simpeler dan row-level parsing

2. **Accepteer incomplete data**
   - Niet elke spec is herkenbaar
   - Sla alles op in "Alle Regelitems Detail" als fallback
   - Laat verkoper in Airtable aanvullen

3. **Prioriteer flexibiliteit**
   - Hardcode geen vaste patterns
   - Gebruik keyword matching met fallbacks
   - Log unparsable content voor review

4. **Test met edge cases**
   - Proposals met 1 table
   - Proposals met 15+ tables
   - Tables met alleen opties (geen hoofdproduct)
   - Kortingen als aparte rows

