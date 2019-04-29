import requests

resp = requests.head("http://localhost/httptest/wikipedia_russia.html")
print(resp.content)