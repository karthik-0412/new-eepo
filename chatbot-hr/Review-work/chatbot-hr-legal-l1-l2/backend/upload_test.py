import httpx

with open('upload_test.txt','wb') as f:
    f.write(b'Test upload from script')

with open('upload_test.txt','rb') as f:
    files = {'file': ('upload_test.txt', f, 'text/plain')}
    resp = httpx.post('http://localhost:8000/api/files/upload', files=files)
    print('status', resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)
