#!/usr/bin/env python3
import json
from gst_service import GSTService

# Load the existing GST data
with open('json-gst_extractor/gst_details_24AAXFA5297L1ZN_20251107_114644.json', 'r') as f:
    gst_data = json.load(f)

print('📥 Loading existing GST data into database...')
print(f'Company: {gst_data.get("legal_name")}')
print(f'GSTIN: {gst_data.get("gstin")}')

# Initialize GST service and store the data
gst_service = GSTService()
gst_id = gst_service.db.store_gst_data(gst_data)
print(f'✅ Stored GST data with ID: {gst_id}')

# Test validation
is_valid, retrieved_data = gst_service.validate_company_gstin('24AAXFA5297L1ZN', 'ARIHANT TRADE WORLD')
print(f'✅ Validation result: {is_valid}')
if is_valid:
    print(f'   Legal Name: {retrieved_data.get("legal_name")}')
    print(f'   Match Score: {retrieved_data.get("name_match_score", "N/A")}')

gst_service.close()