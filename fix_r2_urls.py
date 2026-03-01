#!/usr/bin/env python
"""
Fix existing content_media entries that have private R2 URLs.
Replaces private r2.cloudflarestorage.com URLs with public CDN URL.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ott_backend.settings')
django.setup()

from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
r2_account_id = os.getenv('R2_ACCOUNT_ID')
r2_bucket = os.getenv('R2_BUCKET_NAME')
r2_public_domain = os.getenv('R2_PUBLIC_DOMAIN', '').rstrip('/')

if not all([supabase_url, supabase_key, r2_account_id, r2_public_domain]):
    print("[ERROR] Missing environment variables. Check .env file.")
    exit(1)

private_prefix = f"https://{r2_account_id}.r2.cloudflarestorage.com/{r2_bucket}/"

print(f"Connecting to Supabase: {supabase_url}")
print(f"Replacing: {private_prefix}")
print(f"      With: {r2_public_domain}/")
print()

supabase = create_client(supabase_url, supabase_key)

# Fetch all content_media entries with private R2 URLs
response = supabase.table('content_media').select('id, content_id, media_type, file_url').execute()

fixed = 0
skipped = 0
failed = 0

for entry in response.data:
    file_url = entry.get('file_url', '')
    if not file_url or private_prefix not in file_url:
        skipped += 1
        continue

    new_url = file_url.replace(private_prefix, f"{r2_public_domain}/")
    print(f"[FIX] {entry['media_type']} | {entry['content_id']}")
    print(f"  OLD: {file_url}")
    print(f"  NEW: {new_url}")

    try:
        supabase.table('content_media').update({'file_url': new_url}).eq('id', entry['id']).execute()
        print(f"  [OK] Updated successfully")
        fixed += 1
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        failed += 1

print()
print("=" * 60)
print(f"Fixed:   {fixed}")
print(f"Skipped: {skipped}")
print(f"Failed:  {failed}")
print("=" * 60)
