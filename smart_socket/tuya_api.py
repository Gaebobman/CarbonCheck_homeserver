from enum import Enum
import hashlib
import hmac
import json
import requests
import sys
import urllib3
import time
from tuya_config import *
from typing import Any

"""
This code is based on https://github.com/tuya/tuya-iot-python-sdk by tuya

The MIT License (MIT)

Copyright (c) 2014-2021 Tuya Inc.
Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
DEALINGS IN THE SOFTWARE.
"""

"""
Modified by https://github.com/Gaebobman (Standard Lee)

Create tuya_config.py  in the same directory as get_access_token.py
OR Uncomment the following lines and enter the values of 'Access ID' and 'Access Key' 
shown in the Authorization Key section on the Cloud Development Platform
"""
# CLIENT_ID = "YOUR_ACCESS_ID"
# SECRET = "YOUR_ACCESS_KEY"
# DEVICE_ID = "YOUR_DEVICE_ID"
TO_C_CUSTOM_TOKEN_API = "/v1.0/iot-03/users/login"
TO_C_SMART_HOME_TOKEN_API = "/v1.0/iot-01/associated-users/actions/authorized-login"
BASE_URL = "https://openapi.tuyaus.com/v1.0" # 

class AuthType(Enum):
    """Tuya Cloud Auth Type."""

    SMART_HOME = 0
    CUSTOM = 1


class TuyaTokenInfo:
    """Tuya token info.

    Attributes:
        access_token: Access token.
        expire_time: Valid period in seconds.
        refresh_token: Refresh token.
        uid: Tuya user ID.
        platform_url: user region platform url
    """

    def __init__(self, token_response = None):
        """Init TuyaTokenInfo."""
        result = token_response.get("result", {})

        self.expire_time = (
            token_response.get("t", 0)
            + result.get("expire", result.get("expire_time", 0)) * 1000
        )
        self.access_token = result.get("access_token", "")
        self.refresh_token = result.get("refresh_token", "")
        self.uid = result.get("uid", "")
        self.platform_url = result.get("platform_url", "")


    def _print_informations(self):
        print(f"EXPIRE_TIME: {self.expire_time}\nACCESS_TOKEN: {self.access_token}\nREFRESH_TOKEN: {self.refresh_token}\nUID: {self.uid}\nPLATFORM_URL:{self.platform_url}")


class TuyaOpenAPI:
    """Open Api.

    Typical usage example:

    openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_KEY)
    """

    def __init__(
        self,
        endpoint: str,
        access_id: str,
        access_secret: str,
        auth_type: AuthType = AuthType.SMART_HOME,
        lang: str = "en",
    ) -> None:
        """Init TuyaOpenAPI."""
        self.session = requests.session()

        self.endpoint = endpoint
        self.access_id = access_id
        self.access_secret = access_secret
        self.lang = lang

        self.auth_type = auth_type
        if self.auth_type == AuthType.CUSTOM:
            self.__login_path = TO_C_CUSTOM_TOKEN_API
        else:
            self.__login_path = TO_C_SMART_HOME_TOKEN_API

        self.token_info: TuyaTokenInfo = None

        self.dev_channel: str = ""

        self.__username = ""
        self.__password = ""
        self.__country_code = ""
        self.__schema = ""
    #https://developer.tuya.com/en/docs/iot/singnature?id=Ka43a5mtx1gsc
    def _calculate_sign(self, method:str, path:str, params= None, body=None,
        ):
        # HTTPMethod
            str_to_sign = method
            str_to_sign += "\n"

            # Content-SHA256 / sha256 of pre-request Script
            content_to_sha256 = (
                "" if body is None or len(body.keys()) == 0 else json.dumps(body)
            )
            str_to_sign += (
            # Corresponds to CryptoJS.SHA256(str)
            hashlib.sha256(content_to_sha256.encode("utf8")).hexdigest().lower()
            )
            str_to_sign += "\n"

            # Header
            str_to_sign += "\n"

            # URL
            str_to_sign += path

            # toJsonObj of pre-request Script
            if params is not None and len(params.keys()) > 0:
                str_to_sign += "?"

                params_keys = sorted(params.keys())
                query_builder = "".join(f"{key}={params[key]}&" for key in params_keys)
                str_to_sign += query_builder[:-1]

            # Sign
            t = int(time.time() * 1000)

            message = CLIENT_ID
            if self.token_info is not None:
                message += self.token_info.access_token
            message += str(t) + str_to_sign
            sign = (
                hmac.new(
                    self.access_secret.encode("utf8"),
                    msg=message.encode("utf8"),
                    digestmod=hashlib.sha256,
                )
                .hexdigest()
                .upper()
            )
            return sign, t
    
    # Business verification calculation
    # easy_access_token,"GET","/v1.0/devices?", device_id,"&page_no=1&page_size=20")
    def _calculate_sign_business(self, easy_access_token, method, path, device_id, param_str):
        # Goal: Generate GET\n{CryptoJS.SHA256("")}\n\n/v1.0/devices?device_ids=DEVICE_ID&page_no=1&page_size=20
        str_to_sign = method
        str_to_sign += "\n" # " "GET\n
        # 1. Generate {CryptoJS.SHA256("")}
        content_to_sha256 = ""
        str_to_sign += (
        # Corresponds to CryptoJS.SHA256(str) / This value is always same
        hashlib.sha256(content_to_sha256.encode("utf8")).hexdigest().lower()
        )
        str_to_sign += "\n\n" # " "GET\n{CryptoJS.SHA256("")}\n\n
        str_to_sign += path
        str_to_sign += device_id + param_str
        print(str_to_sign)
        t = int(time.time() * 1000)
        str_hash = CLIENT_ID + easy_access_token + str(t) +str_to_sign
        print(str_hash)
        sign = (
            hmac.new(
                self.access_secret.encode("utf8"), 
                msg=str_hash.encode("utf8"), 
                digestmod=hashlib.sha256,
            )
            .hexdigest()
            .upper()
        )

        return sign, t


def get_token(sign, t):
    url = BASE_URL + "/token?grant_type=1"
    payload = {}
    headers = {
        'client_id': CLIENT_ID,
        'sign': sign,
        't': str(t),
        'sign_method': 'HMAC-SHA256',
        'nonce': '',
        'stringToSign': ''
    }
    
    response =requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_devices_information(easy_access_token, sign, t, device_id, http):
    url = BASE_URL + f"/devices?device_ids={device_id}&page_no=1&page_size=20"
    headers = {
        'client_id': CLIENT_ID,
        'access_token': easy_access_token,
        'sign': sign,
        't': str(t),
        'sign_method': 'HMAC-SHA256'
    }
    
    response = http.request("GET", url, headers=headers)
    return json.loads(response.data)


def control_device(easy_access_token, sign, t, device_id, action):
    url = BASE_URL + f"/devices/{device_id}/commands"
    # print(f'\nurl: {url}\nsign: {sign}\naction: {action}\n')
    headers = {
        'client_id': CLIENT_ID,
        'access_token': easy_access_token,
        'sign': sign,
        't': str(t),
        'sign_method': 'HMAC-SHA256',
        'Content-Type': 'application/json'
    }

    body={
        'commands':[
            {
                'code': 'switch_1',
                'value': action
            }
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    print(result)
    result = result['success']
    print(result)
    

def parse_information(device_id, response):
    device_info = response.get("result", {}).get("devices", [])
    if not device_info:
        return None
    item = device_info[0]
    # name = item.get("name")
    name = device_id
    status = item.get("status")
    # codes = {"switch_1","cur_current", "cur_power", "cur_voltage", "add_ele"}
    codes = {"add_ele"}
    values = {item.get("code"): item.get("value") for item in status if item.get("code") in codes}
    return {"plug_id": name, **values}


def send_information_to_server(device_information):
    headers = {"Content-Type": "application/json"}
    device_information["amount"] = device_information["add_ele"]
    del device_information["add_ele"]
    message = json.dumps(device_information)
    print(f'{headers}\n{message}')
    try:
        response = requests.post(f"https://{ELECTRICITY_USAGE_CLIENT}", headers=headers, data=message)
        result = response.json()
        result = result['success']
        return result
    except Exception as e:
        return False


def main():
    http = urllib3.PoolManager()
    openapi = TuyaOpenAPI("https://openapi.tuyaus.com", CLIENT_ID, SECRET)
    sign, t = openapi._calculate_sign("GET","/v1.0/token?grant_type=1")
    openapi.token_info = TuyaTokenInfo(get_token(sign, t))
    easy_access_token = openapi.token_info.access_token

    if len(sys.argv) == 1: 
        # Send data mode
        device_list = [SOCKET_0_ID, SOCKET_1_ID, SOCKET_2_ID, SOCKET_3_ID]
        for device_id in device_list:
            sign, t = openapi._calculate_sign_business(easy_access_token,"GET","/v1.0/devices?device_ids=", device_id,"&page_no=1&page_size=20")
            res = get_devices_information(easy_access_token, sign, t, device_id, http)
            print(send_information_to_server(parse_information(device_id,res)))
    else:
        # Command mode (tuya_api.py {device_id} {bool})

        sign, t = openapi._calculate_sign_business(easy_access_token,"POST","/v1.0/devices/", sys.argv[1],"/commands")
        action = sys.argv[2].lower() == 'true'
        control_device(easy_access_token, sign, t, sys.argv[1], action)


if __name__=="__main__":
    main()
