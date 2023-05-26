import multiprocessing as mp
import sseclient
import threading
import time
import requests
import subprocess
import sys
from config.database_config import *
from typing import Optional


# Define python file names
DETECT_PY = './detect_user.py'
UDP_PY = './server_udp.py'
TRAIN_PY = './train_faces.py'
SEND_WATER_PY = './update_data_and_send.py'
SEND_ELECTRICITY_PY ='./smart_socket/tuya_api.py'

"""
# Define a function to run as a process
def print_name(name: str, arg: Optional[str] = None):
    print(f"Process {name} started with argument {arg}")
    while True:
        time.sleep(1)
"""
# Define a function to terminate a process
def terminate_process(process_name):
    # Check if the process is alive
    if processes[process_name].is_alive():
        # Terminate the process
        processes[process_name].terminate()
        # Wait for the process to end
        processes[process_name].join()


# Define a function to execute a subprocess
def worker(filename, arg: Optional[str] = None):
    print(f"Process {filename} started with argument {arg}")
    subprocess.run([sys.executable, filename, arg])


# Define a function to run as a SSE client
def sse_client(url: str, headers: dict):
    # Create a SSE client object
    response = requests.get(url, stream=True, headers=headers)
    client = sseclient.SSEClient(response)
    # Receive events from the server
    for event in client.events():
        # Check the event data
        data = event.data
        if data.startswith("ADD USER"):
            # Extract the user_id from the data
            user_id = data.split()[2]
            terminate_process(DETECT_PY)
            # Create and start the train_faces.py process with user_id as argument
            processes[TRAIN_PY] = mp.Process(target=worker, args=(TRAIN_PY, user_id))
            processes[TRAIN_PY].start()
        elif data == "TRAINING DONE":
           # TRAIN_PY 종료
            terminate_process(TRAIN_PY)
            # Create and start the DETECT_PY process
            processes[DETECT_PY] = mp.Process(target=worker, args=(DETECT_PY,))
            processes[DETECT_PY].start()

# Define a main function to run the main features
def main():
    # Create a dict to store processes
    global processes
    processes = {}

    # Create and start the DETECT_PY and UDP_PY processes
    processes[DETECT_PY] = mp.Process(target=worker, args=(DETECT_PY,))
    processes[UDP_PY] = mp.Process(target=worker, args=(UDP_PY,))
    processes[DETECT_PY].start()
    processes[UDP_PY].start()

    # Record the last time the update_data_and_send.py process was executed
    last_update_time = time.time()

    # Create and start a thread to run as a SSE client
    url = SSE_CLIENT_URL
    headers = {'Accept': 'text/event-stream'}
    sse_thread = threading.Thread(target=sse_client, args=(url, headers))
    sse_thread.start()

    # Repeat the following steps indefinitely
    while True:
        # 5분마다 업데이트 되어야 하므로 5분이 되었는지 확인한다.
        if time.time() - last_update_time > 300:
            # Create and start the update_data_and_send.py process
            processes[SEND_WATER_PY] = mp.Process(target=SEND_WATER_PY, args=(SEND_WATER_PY,))
            processes[SEND_WATER_PY].start()
            # Record the current time as the last update time
            last_update_time = time.time()


if __name__ == "__main__":
    main()
