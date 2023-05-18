import config.py
import time
import pymysql
import logging
import re
from websocket import create_connection


logging.basicConfig(filename="log/communication_log.txt", level=logging.INFO) # Set log file
BATCH_SIZE = 10    # Batch size of tuples

# 1. Update table using visitor info / Guess user_id by Enterance time / Replace Null with visitor_info.user_id  
def update_water_usage():
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
    try:
        curs = conn.cursor()
        query = """ SELECT visitor_info.user_id, water_usage.usage_id, water_usage.start_time, 
MIN(ABS(TIMESTAMPDIFF(SECOND, visitor_info.enterance_time, water_usage.start_time))) AS diff
From visitor_info INNER JOIN water_usage ON visitor_info.user_id <> water_usage.user_id AND visitor_info.enterance_time < water_usage.start_time
GROUP BY water_usage.usage_id"""
        curs.execute(query)
        # fetch result of query
        data = curs.fetchall()
        # update water_usage
        for row in data:
            user_id = row[0]
            usage_id = row[1]
            start_time = row[2]
            diff = row[3]
            update_query = "UPDATE water_usage SET user_id = %s WHERE usage_id = %s"
            curs.execute(update_query, (user_id, usage_id))
        conn.commit()
    finally: 
        conn.close()

# 2. Send it to server (Every 5 minutes)
def send_record_to_server():
    sent_range = find_sent_range()
    query = "SELECT usage_id, user_id, start_time, end_time, place, amount FROM water_usage"
    if sent_range:
        min_usage_id, max_usage_id = sent_range
        query = "SEELCT usage_id, user_id, start_time, end_time, place, amount from water_usage WHERE usage_id NOT BETWEEN %s AND %s"
    
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
    try:
        curs = conn.cursor()
        curs.execute(query)
        data = curry.fetchall()
        ws = websocket.creat_connection(f"ws:{CARBONCHECK_SERVER_URL}")
    finally:conn.close()

    user_id = row[0]
    usage_id = row[1]
    start_time = row[2]
    end_time = row[3]
    place = row[4]
    amount = row[5]
    message = str(row)

    try:
        ws.send(message)
        # update min, max _usage_id
        if min_usage_id is None or usage_id < min_usage_id:
            min_usage_id = usage_id
        if max_usage_id is None or usage_id > max_usa
e_id:
            max_usage_id = usage_id
        return True, min_usage_id, max_usage_id
    except Exception as e:
        return False, min_usage_id, max_usage_id
    
    

# 3. Log the size of the column you sent and the response you received from the server
def save_log(row, result):
    user_id = row[0]
    usage_id = row[1]
    start_time = row[2]
    end_time = row[3]
    place = row[4]
    amount = row[5]
    message = str(row)
    if result:
        logging.info(f"Sent {message} to the server")
    else:
        logging.error(f"Failed to send {message} to the server")

# 4. Read the log and decide whether to resend or not
def communication_result():
    # return False
    return True

# service function for checking sent row number
def find_sent_range():
    with open("log.txt", "r") as f:
        last_line = f.readlines()[-1]
        match = re.search(r"usage_id from (\d+) to (\d+)", last_line) 
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        return None


def main():
    # 1. Update table using visitor info / Guess user_id by Enterance time / Replace Null with visitor_info.user_id
    update_water_usage() 
    # 2. Send it to server 
    send_record_to_server()

    # 3. Log the size of the column you sent and the response you received from the server
    communication_log()
    # 4. Read the log and decide whether to resend or not
    if (communication_result() == False):
            
        
        



if __name__ == "__main__":
    main()

