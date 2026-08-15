import requests
import time

# Wait for server to be ready
time.sleep(3)

# Test upload
with open('test_upload.log', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/v1/upload',
        files={'file': ('auth_test.log', f)},
        data={'caseId': 'CASE-1042'}
    )

print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')

if response.status_code == 200:
    data = response.json().get('data', {})
    print(f'\nSuccess!')
    print(f'Filename: {data.get("filename")}')
    print(f'Job ID: {data.get("jobId")}')
    print(f'Parse Status: {data.get("parseStatus")}')
    print(f'Event Count: {data.get("eventCount")}')
else:
    print(f'\nError: {response.json().get("message")}')
