import json
import urllib.request

url = 'http://localhost:8000/api/process-video'
data = json.dumps({
    'youtube_url': 'https://www.youtube.com/watch?v=lCTppnE8I_c',
    'topic': 'General',
    'level': 'middle'
}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as resp:
    print(resp.status)
    print(resp.read().decode('utf-8'))
