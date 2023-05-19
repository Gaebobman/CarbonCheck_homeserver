import socket
import time
import pymysql
from config.database_config import *


def insert_data(usage_data):
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, 
                           password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')

    try:
        curs = conn.cursor()
        sql = "INSERT INTO water_usage(user_id, START_TIME, END_TIME, PLACE, AMOUNT)  VALUES (%s, %s, %s, %s, %s)"
        curs.execute(sql, usage_data)
        conn.commit()
    finally: 
        conn.close()


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


# Create a UDP socket
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('10.42.0.1', 18999)
server.bind(server_address)
flow_rate_sum = 0.0
flow_rate_count = 0
current_flow_rate = 0.0
start, end = time.time(), time.time()
place = "FLOW1" # Name of water outlet
print("Listening...")
# Receive and print the flow rate data from the Arduino every 2 seconds
while True:
        data, address = server.recvfrom(1024)
        data = data.decode()
        # TODO: SPLIT STRING : PLACE USAGE 
        current_flow_rate = float(data)   # L / min
        print(f"Flow rate: {current_flow_rate} L/min")

        if (current_flow_rate == 0.0):
            end = time.time()
            if(flow_rate_count > 0):    
                # (Mean per minute) / 60 * (Seconds ) 
                water_usage = (flow_rate_sum / flow_rate_count) / 60 * (end - start)
                formatted_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start))
                formatted_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end))
                print(f"Water usage from {formatted_start} to {formatted_end}: {water_usage}")
                # pymysql INSERT
                insert_data((None, formatted_start, formatted_end, place, water_usage))
                flow_rate_sum = 0.0
                flow_rate_count = 0
        elif (current_flow_rate > 0.0):
            if(flow_rate_count == 0):
                start = time.time()
                flow_rate_sum += current_flow_rate
                flow_rate_count += 1
            else:
                flow_rate_sum += current_flow_rate
                flow_rate_count += 1

