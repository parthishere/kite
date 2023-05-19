
import requests
import json
from time import sleep

url1 = "http://127.0.0.1:8000/api/stopAlgo/"
url2 = "http://127.0.0.1:8000/api/startAlgo/"
array_instrument = ["NYKAA", "KEC", "UBL", "FEDERALBNK", "SBIN"]

def start(delay):
    for i in array_instrument:
        sleep(delay);
        payload = json.dumps({
        "instrument": i,
        "instrumentQuantity": 1,
        "is_algo": True
        })
        headers = {
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url2, headers=headers, data=payload)
        print(response.text)

def stop(delay):
    for i in array_instrument:
        sleep(delay);
        payload = json.dumps({
            "instrument": i,
            "instrumentQuantity": 0,
            "is_algo": True
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url1, headers=headers, data=payload)

        print(response.text)

if __name__ == "__main__":
    while True:
        try:
          a, b = str(input("enter 's' or 't' to start and stop and with space enter delay: (example: 's 0.2') ")).lower().split(" ")
        except:
          break;
        # b = float(input("enter delay: "))
        if a == "s":
            start(float(b))
        elif a == "t":
            stop(float(b))
        else:
            break;