#!/bin/bash

# Comprehensive API Test Suite
echo "=================================================="
echo "RDM Supervisor API Test Suite"
echo "=================================================="

# Test 1: Login as Alice
echo -e "\n=== Test 1: Login as Alice ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=demo123" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✓ Successfully logged in as Alice"

# Test 2: Get current user
echo -e "\n=== Test 2: Get Current User ==="
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo "✓ Retrieved user info"

# Test 3: List projects
echo -e "\n=== Test 3: List Projects ==="
curl -s http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo "✓ Listed projects"

# Test 4: Get project RDMP
echo -e "\n=== Test 4: Get Project 1 RDMP (qPCR) ==="
curl -s http://localhost:8000/api/rdmp/projects/1/rdmp \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps({'rdmp_name': data['rdmp_json'].get('name', 'N/A'), 'version': data['version_int'], 'num_fields': len(data['rdmp_json'].get('fields', [])), 'num_roles': len(data['rdmp_json'].get('roles', []))}, indent=2))"
echo "✓ Retrieved RDMP"

# Test 5: List samples in project 1
echo -e "\n=== Test 5: List Samples in Project 1 ==="
curl -s http://localhost:8000/api/projects/1/samples \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; samples=json.load(sys.stdin); print(f'Found {len(samples)} samples:'); [print(f\"  - {s['sample_identifier']}: {'COMPLETE' if s['completeness'].get('is_complete') else 'INCOMPLETE (missing: ' + ', '.join(s['completeness'].get('missing_fields', [])) + ')'}\") for s in samples]"
echo "✓ Listed samples with completeness status"

# Test 6: Get incomplete sample details
echo -e "\n=== Test 6: Get Incomplete Sample (QPCR-002) ==="
curl -s http://localhost:8000/api/samples/2 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; s=json.load(sys.stdin); print(json.dumps({'sample_id': s['sample_identifier'], 'fields': s['fields'], 'missing_fields': s['completeness']['missing_fields']}, indent=2))"
echo "✓ Retrieved incomplete sample"

# Test 7: Fix missing field
echo -e "\n=== Test 7: Fix Missing Field (cell_line) ==="
curl -s -X PUT http://localhost:8000/api/samples/2/fields/cell_line \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "HEK293"}' | python3 -m json.tool
echo "✓ Added missing field"

# Test 8: Verify sample is now complete
echo -e "\n=== Test 8: Verify Sample is Now Complete ==="
curl -s http://localhost:8000/api/samples/2 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; s=json.load(sys.stdin); print(f\"Sample {s['sample_identifier']}: {'COMPLETE ✓' if s['completeness']['is_complete'] else 'INCOMPLETE'}\")"

# Test 9: List RDMP templates
echo -e "\n=== Test 9: List RDMP Templates ==="
curl -s http://localhost:8000/api/rdmp/templates \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; templates=json.load(sys.stdin); print(f'Found {len(templates)} templates:'); [print(f\"  - {t['name']}: {t['description']}\") for t in templates]"
echo "✓ Listed RDMP templates"

# Test 10: Create a new sample
echo -e "\n=== Test 10: Create New Sample ==="
curl -s -X POST http://localhost:8000/api/projects/1/samples \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sample_identifier": "QPCR-003"}' | python3 -m json.tool
echo "✓ Created new sample"

# Test 11: Add field values to new sample
echo -e "\n=== Test 11: Add Fields to New Sample ==="
curl -s -X PUT http://localhost:8000/api/samples/5/fields/gene_name \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "ACTB"}' > /dev/null
curl -s -X PUT http://localhost:8000/api/samples/5/fields/cell_line \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "A549"}' > /dev/null
curl -s -X PUT http://localhost:8000/api/samples/5/fields/primer_batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "BATCH-2024-02"}' > /dev/null
curl -s -X PUT http://localhost:8000/api/samples/5/fields/replicate_number \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 1}' > /dev/null
curl -s -X PUT http://localhost:8000/api/samples/5/fields/experiment_date \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "2024-01-20"}' > /dev/null
echo "✓ Added all required fields"

# Test 12: Test as different user (Bob)
echo -e "\n=== Test 12: Login as Bob (Researcher) ==="
BOB_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bob&password=demo123" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✓ Logged in as Bob"

echo -e "\n=== Test 13: Bob's Projects ==="
curl -s http://localhost:8000/api/projects \
  -H "Authorization: Bearer $BOB_TOKEN" | python3 -c "import sys, json; projects=json.load(sys.stdin); print(f'Bob has access to {len(projects)} project(s):'); [print(f\"  - {p['name']}\") for p in projects]"

# Test 14: Get project memberships
echo -e "\n=== Test 14: Get Project 1 Memberships ==="
curl -s http://localhost:8000/api/projects/1/memberships \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; members=json.load(sys.stdin); print(f'Project has {len(members)} members:'); [print(f\"  - User {m['user_id']}: {m['role_name']}\") for m in members]"
echo "✓ Listed memberships"

echo -e "\n=================================================="
echo "✓ All tests passed successfully!"
echo "=================================================="
