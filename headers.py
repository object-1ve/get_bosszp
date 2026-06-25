import requests


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.zhipin.com",
    "priority": "u=1, i",
    "referer": "https://www.zhipin.com/web/geek/jobs?query=agent%E5%BC%80%E5%8F%91&city=101210700&industry=&position=",
    "sec-ch-ua": "\"Google Chrome\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "token": "4Gp9NzxHchORpTmR",
    "traceid": "F-0019eff16bdb0fCoHPILAH",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "zp_token": "V2Rt4hGO3-3l1uVtRuxx4ZICq27DrRwi0~|Rt4hGO3-3l1uVtRuxx4ZICq27DrRwyU~"
}
cookies = {
    "lastCity": "101210700",
    "__g": "-",
    "Hm_lvt_194df3105ad7148dcf2b98a91b5e727a": "1782392159",
    "HMACCOUNT": "559211D9059B35F8",
    "ab_guid": "6173aa68-a750-4447-b4a8-c44553737cc3",
    "__l": "l=%2Fwww.zhipin.com%2Fwenzhou%2F%3FseoRefer%3Dindex&r=&g=&s=3&friend_source=0&s=3&friend_source=0",
    "Hm_lpvt_194df3105ad7148dcf2b98a91b5e727a": "1782395961",
    "wt2": "DxrPNSah1CbsK1E4UOEHxg7bLfbGpxXY2E9hsD3SbEa9n10J9KE6ALFn_DVO85Z_x1NDJ3lUTgmYbevhttzW2Vg~~",
    "wbg": "0",
    "zp_at": "4iyWXR3bDFFKEe4GfQpeuwq8S_nU9lXO6MCg0ASzLlI~",
    "__zp_stoken__": "71f3gQDjDhsK5w67DgT8pDzhAJEE0OUA4NzI7QDhkJD09NTZBOB8fw5YFfFvDhcKJwr1DLzg3QUBAOjc0Nx84Qzk9QD80OcS6wr09NDnCsUMoEhbDnRF0XMOJEW7CuALDpcK9ETYCMsOAERkrKQURCQ4MYWMGEwRXEVtSYGAHBlIEY2FbB2BXAlgGEw4CFRc6wp3CtDXCvEnCtD3Dg0bDgD3CuzU2OT0tOVbCqS0dPDQ0QDU2xLnEtsS6xLrEt8S5xLbEusOCw7LDncS2xLrEusKyxLnEtsS6w7rDksS5xLbEusS6w7XCti9AwpHCtcOJxbTDh8KcxJ3FqMOOwqjEnMOiw5%2FCh8OJw6%2FDlMKVxLrEg8Ohw4DDosODxK3Cp8S3wr3Dv8KZxLLCs8SywozCiMKXw73DgMOCw4DDjF7Dv0rDsVbCm1HDpcK%2FwpjCr8O9XMKiUcO4bcK%2BwqrDv8Kmw7VQwovCrsKnU0LCtsKbwrXCiWlVZsK%2Ff8Kkwq1deUdWc8OBWm5Jb8K6a8ODamcHWxFdDgg5UsOIw4bDhA%3D%3D",
    "__c": "1782392159",
    "__a": "90051984.1782392159..1782392159.16.1.16.16",
    "bst": "V2Rt4hGO3-3l1uVtRuxx4ZICq27DrRwi0~|Rt4hGO3-3l1uVtRuxx4ZICq27DrRwyU~"
}
url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
params = {
    "_": "1782396140976"
}
data = {
    "page": "1",
    "pageSize": "15",
    "city": "101210700",
    "query": "agent开发",
    "expectInfo": "",
    "multiSubway": "",
    "multiBusinessDistrict": "",
    "position": "",
    "jobType": "",
    "salary": "",
    "experience": "",
    "degree": "",
    "industry": "",
    "scale": "",
    "stage": "",
    "scene": "1",
    "encryptExpectId": ""
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)