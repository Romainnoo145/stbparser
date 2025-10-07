#!/usr/bin/env python3
"""Add sample products to Product Catalogus to demonstrate the system."""

import requests
from backend.core.settings import settings

API_KEY = settings.airtable_api_key
SALES_BASE_ID = settings.airtable_base_stb_sales

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Sample products based on common items in STB quotes
SAMPLE_PRODUCTS = [
    {
        "Product Naam": "Hordeur Standaard",
        "Product ID": "HOR-STD-001",
        "Categorie": "Hordeur",
        "Standaard Kostprijs": 125.00,
        "Eenheid": "Stuk",
        "Leverancier": "Horren Fabrikant",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "hordeur,hor,standaard,insect screen",
        "Notities": "Standaard hordeur voor ramen, meest verkochte model"
    },
    {
        "Product Naam": "HR++ Glas 4-16-4",
        "Product ID": "GLAS-HR-416",
        "Categorie": "Glas",
        "Standaard Kostprijs": 45.50,
        "Eenheid": "m²",
        "Leverancier": "GlasPartner",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "hr++ glas,dubbel glas,isolatieglas,4-16-4",
        "Notities": "Standaard HR++ isolatieglas, meest gebruikte glassoort"
    },
    {
        "Product Naam": "Beslag Set Standaard",
        "Product ID": "BESLAG-SET-001",
        "Categorie": "Beslag",
        "Standaard Kostprijs": 35.00,
        "Eenheid": "Set",
        "Leverancier": "Beslag BV",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "beslag,beslag set,handvat,sluiting",
        "Notities": "Standaard beslagset voor ramen en deuren"
    },
    {
        "Product Naam": "Dorpel Aluminium 100cm",
        "Product ID": "DORPEL-AL-100",
        "Categorie": "Onderdeel",
        "Standaard Kostprijs": 28.50,
        "Eenheid": "Stuk",
        "Leverancier": "Metaal Leverancier",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "dorpel,drempel,aluminium dorpel,100cm",
        "Notities": "Aluminium buitendorpel 100cm lengte"
    },
    {
        "Product Naam": "Profiel Kunststof Wit",
        "Product ID": "PROFIEL-KS-WIT",
        "Categorie": "Profiel",
        "Standaard Kostprijs": 15.00,
        "Eenheid": "m¹",
        "Leverancier": "Profiel Fabriek",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "profiel,kunststof profiel,wit profiel,pvc",
        "Notities": "Kunststof kozijnprofiel wit, standaard kwaliteit"
    },
    {
        "Product Naam": "Kit Wit 310ml",
        "Product ID": "KIT-WIT-310",
        "Categorie": "Onderdeel",
        "Standaard Kostprijs": 4.50,
        "Eenheid": "Stuk",
        "Leverancier": "Bouwmaterialen BV",
        "Actief": True,
        "Bron": "Handmatig",
        "Matching Keywords": "kit,kitspuit,wit,310ml,afdichtingskit",
        "Notities": "Witte afdichtingskit voor kozijnen, 310ml koker"
    },
]


def add_sample_products():
    """Add sample products to Product Catalogus."""

    url = f"https://api.airtable.com/v0/{SALES_BASE_ID}/Product Catalogus"

    print("="*60)
    print("ADDING SAMPLE PRODUCTS TO PRODUCT CATALOGUS")
    print("="*60)

    payload = {
        "records": [{"fields": product} for product in SAMPLE_PRODUCTS],
        "performUpsert": {
            "fieldsToMergeOn": ["Product ID"]
        }
    }

    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        result = response.json()
        count = len(result.get("records", []))

        print(f"\n[OK] Added {count} sample products:\n")

        for product in SAMPLE_PRODUCTS:
            name = product["Product Naam"]
            price = product.get("Standaard Kostprijs", 0)
            unit = product.get("Eenheid", "Stuk")
            print(f"  - {name}")
            print(f"      Price: EUR {price} per {unit}")
            print(f"      ID: {product['Product ID']}")
            print()

        print("="*60)
        print("SAMPLE PRODUCTS ADDED SUCCESSFULLY")
        print("\nNext steps:")
        print("  1. View products in Airtable STB-SALES base")
        print("  2. Add more products or update prices as needed")
        print("  3. Test product matching in Offorte sync")
        print("="*60)

        return count
    else:
        print(f"[FAIL] Failed to add products: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error: {error_detail}")
        except:
            print(f"Response: {response.text}")
        return 0


if __name__ == "__main__":
    add_sample_products()
