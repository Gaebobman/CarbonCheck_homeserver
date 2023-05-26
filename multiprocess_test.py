# TEST ONLY
import multiprocessing as mp
import subprocess
import sys
import time
from typing import Optional



SEND_ELECTRICITY_PY ='./smart_socket/tuya_api.py'
DUMMY_PY ='./DUMMY.py'

# Define a function to execute a subprocess
def worker(filename, arg: Optional[str] = None):
    print(f"Process {filename} started with argument {arg}")
    if arg is not None:
        subprocess.run([sys.executable, filename, arg])
    else:
        subprocess.run([sys.executable, filename])


# Define a function to terminate a process
def terminate_process(process_name):
    # Check if the process is alive
    if processes[process_name].is_alive():
        # Terminate the process
        processes[process_name].terminate()
        # Wait for the process to end
        processes[process_name].join()


def main():
    global processes
    processes = {}
    # Create and start the UDP_PY and SEND_ELECTRICITY_PY processes

    processes[SEND_ELECTRICITY_PY] = mp.Process(target=worker, args=(SEND_ELECTRICITY_PY,))
    processes[SEND_ELECTRICITY_PY].start()
    processes[DUMMY_PY] =  mp.Process(target=worker, args=(DUMMY_PY, "I'm Dummy and I'm happy happy"))
    processes[DUMMY_PY].start()
    start_time = time.time()
    while(True):
        for process in processes:
            if processes[process].is_alive():
                print(process, " IS alive")
            else:
                terminate_process(process)
        if time.time() - start_time > 30:
            terminate_process(SEND_ELECTRICITY_PY)
            terminate_process(DUMMY_PY)
            break
        time.sleep(1)


if __name__ == "__main__":
    main()