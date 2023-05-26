# TEST ONLY

import json
import pprint
import sseclient
import urllib3 
from config.database_config import *

def with_urllib3(url, headers):
    """Get a streaming response for the given event feed using urllib3."""
    http = urllib3.PoolManager()
    return http.request('GET', url, preload_content=False, headers=headers)

def main():
    url = f'https://{CARBONCHECK_SERVER_URL}/subscribe/{HOME_SERVER_ID}/{HOME_SERVER_ID}'
    headers = {'Accept': 'text/event-stream'}
    client = sseclient.SSEClient(url)
    # response = with_urllib3(url, headers)
    # if response.status == 200:
    #     print("Connected to the server")
    # else:
    #     print("Connection failed: {}".format(response.reason))

    for message in client.events():
        pprint.pprint(json.loads(message.data))

if __name__ == "__main__":
    main()