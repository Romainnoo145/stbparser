#!/usr/bin/env python3
"""Compare proposal patterns between different users to identify variations."""

import requests
import json
from bs4 import BeautifulSoup
from collections import defaultdict
from time import sleep

api_key = "H7EhsUhJ4kEQFM7K7PJJOAgW7WxOpcXJ"
base_url = "https://connect.offorte.com/api/v2/stb-kozijnen"

# Get all won proposals
response = requests.get(f"{base_url}/proposals/won/?api_key={api_key}", timeout=10)
all_proposals = response.json()

# Separate by user
user_proposals = defaultdict(list)
for p in all_proposals:
    user_proposals[p['account_user_id']].append(p)

print(f"Total won proposals: {len(all_proposals)}")
print(f"\nProposals per user:")
for user_id, proposals in user_proposals.items():
    avg_price = sum(float(p['price_total_original']) for p in proposals) / len(proposals)
    print(f"  User {user_id}: {len(proposals)} proposals, avg €{avg_price:,.2f}")

# Analyze top 5 from each major user
patterns = {
    'discount_as_line_item': [],
    'discount_in_product': [],
    'options_as_separate_rows': [],
    'options_in_description': [],
    'product_has_id': [],
    'product_no_id': [],
    'html_patterns': defaultdict(int)
}

for user_id, proposals in user_proposals.items():
    if len(proposals) < 5:
        continue

    # Get top 5 by price
    top_5 = sorted(proposals, key=lambda x: float(x['price_total_original']), reverse=True)[:5]

    print(f"\n{'='*80}")
    print(f"Analyzing User {user_id} (top 5 proposals)")
    print(f"{'='*80}")

    for proposal in top_5:
        try:
            detail_response = requests.get(
                f"{base_url}/proposals/{proposal['id']}/details?api_key={api_key}",
                timeout=10
            )

            if detail_response.status_code != 200:
                continue

            data = detail_response.json()
            print(f"\nProposal {proposal['id']} - {proposal['name']} - {proposal['price_total']}")

            # Analyze structure
            if 'content' in data and 'pricetables' in data['content']:
                total_rows = 0
                rows_with_discount = 0
                rows_with_product_id = 0
                separate_options = 0

                for table_idx, table in enumerate(data['content']['pricetables']):
                    if 'rows' not in table:
                        continue

                    print(f"  Table {table_idx + 1}: {len(table['rows'])} rows, subtotal €{table['subtotal']}")

                    for row in table['rows']:
                        total_rows += 1

                        # Check for discount patterns
                        if row.get('discount_value') and row['discount_value'] != '':
                            rows_with_discount += 1
                            patterns['discount_in_product'].append({
                                'proposal_id': proposal['id'],
                                'user_id': user_id,
                                'discount_type': row.get('discount_type'),
                                'discount_value': row.get('discount_value')
                            })

                        # Check for product_id
                        if row.get('product_id'):
                            rows_with_product_id += 1
                            patterns['product_has_id'].append(proposal['id'])
                        else:
                            patterns['product_no_id'].append(proposal['id'])

                        # Analyze HTML content
                        content = row.get('content', '')
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')

                            # Count patterns
                            bullets = soup.find_all('li')
                            if bullets:
                                patterns['html_patterns']['has_bullets'] += 1
                                patterns['html_patterns'][f'bullets_{len(bullets)}'] += 1

                            # Check for common keywords
                            text = soup.get_text().lower()
                            if 'inclusief' in text:
                                patterns['html_patterns']['has_inclusief'] += 1
                            if 'korting' in text:
                                patterns['html_patterns']['has_korting'] += 1
                            if any(word in text for word in ['triple', 'hr++', 'hr+++', 'glas']):
                                patterns['html_patterns']['mentions_glass'] += 1
                            if any(word in text for word in ['antraciet', 'wit', 'zwart', 'kleur']):
                                patterns['html_patterns']['mentions_color'] += 1

                        # Detect if this is likely a separate option line
                        content_text = BeautifulSoup(content, 'html.parser').get_text().lower() if content else ''
                        if any(keyword in content_text for keyword in ['korting', 'meerprijs', 'toeslag', 'extra']):
                            separate_options += 1

                print(f"    Rows with discount: {rows_with_discount}/{total_rows}")
                print(f"    Rows with product_id: {rows_with_product_id}/{total_rows}")
                print(f"    Separate option rows: {separate_options}/{total_rows}")

            sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"  Error: {e}")

print(f"\n\n{'='*80}")
print("PATTERN SUMMARY")
print(f"{'='*80}")
print(f"Products with ID: {len(set(patterns['product_has_id']))}")
print(f"Products without ID: {len(set(patterns['product_no_id']))}")
print(f"Discount patterns found: {len(patterns['discount_in_product'])}")

print(f"\nHTML Content Patterns:")
for pattern, count in sorted(patterns['html_patterns'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {pattern}: {count}")

# Save detailed findings
with open('/tmp/pattern_analysis.json', 'w') as f:
    # Convert sets to lists for JSON
    patterns['product_has_id'] = list(set(patterns['product_has_id']))
    patterns['product_no_id'] = list(set(patterns['product_no_id']))
    json.dump(patterns, f, indent=2)

print(f"\nDetailed patterns saved to: /tmp/pattern_analysis.json")
