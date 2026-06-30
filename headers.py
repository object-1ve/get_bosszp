import requests


headers = {

}
cookies = {
}
url = "https://www.zhipin.com/wapi/zpgeek/pc/recommend/job/list.json"
params = {
    "page": "1",
    "pageSize": "15",
    "city": "101020100",
    "experience": "108,102,103",
    "encryptExpectId": "",
    "mixExpectType": "",
    "expectInfo": "",
    "jobType": "",
    "salary": "",
    "degree": "",
    "industry": "",
    "scale": "",
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)