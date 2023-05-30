import json
import logging
import re
import time
from datetime import datetime
import pymysql
import requests
from config.database_config import *

logging.basicConfig(filename="log/communication_log.txt", level=logging.INFO) # Set log file
BATCH_SIZE = 10    # Batch size of tuples
min_usage_id, max_usage_id = None, None

# 1. Update table using visitor info / Guess user_id by Enterance time / Replace Null with visitor_info.user_id  
def update_water_usage():
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
    try:
        curs = conn.cursor()
        curs.execute("SET @@global.sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'")
        conn.commit()
        query = """ 
SELECT visitor_info.user_id AS USER_ID, water_usage.usage_id AS USAGE_ID, visitor_info.enterance_time ,water_usage.start_time, MIN(ABS(TIMESTAMPDIFF(SECOND, visitor_info.enterance_time, water_usage.start_time))) AS diff 
FROM visitor_info INNER JOIN water_usage 
ON water_usage.user_id IS NULL  
AND visitor_info.enterance_time < water_usage.start_time
GROUP BY USAGE_ID, USER_ID
"""
        curs.execute(query)
        # fetch result of query
        data = curs.fetchall()
        data_list = sorted(list(data),key=lambda x:(x[1], x[4]))
        user_id, usage_id = None, None
        # update water_usage
        for row in data_list:
            if usage_id == row[1]:
                continue
            user_id = row[0]
            usage_id = row[1]
            update_query = "UPDATE water_usage SET user_id = %s WHERE usage_id = %s"
            curs.execute(update_query, (user_id, usage_id))
        conn.commit()
    finally: 
        conn.close()

# Retrieve data from local database
def get_tuples():
    sent_range = find_sent_range()
    start, end = None, None
    query = "SELECT usage_id,CAST(user_id AS SIGNED), start_time, end_time, place, amount FROM water_usage"
    if sent_range:
        start, end = sent_range
        query = "SELECT usage_id, CAST(user_id AS SIGNED), start_time, end_time, place, amount from water_usage WHERE usage_id NOT BETWEEN %s AND %s"
    
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
    data = None
    try:
        curs = conn.cursor()
        if start is not None:
            curs.execute(query,(min_usage_id, max_usage_id))
        else:
            curs.execute(query)
        data = curs.fetchall()
    finally:
        conn.close()
    return data


def json_datetime_default(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError('not JSON serializable')



# 2. Send data to server / # Retrieve data from local database
def send_data_to_server(rows):
        global min_usage_id, max_usage_id
        # message = str(rows)
        headers = {"Content-Type": "application/json"}
        row_headers = ['user_id', 'start_time', 'end_time', 'place', 'amount']
        json_data = []
        for row in rows:
            if row[1] is not None:
                json_data.append(dict(zip(row_headers, row[1:]))) # Zip the column and tuple elements and make a dictionary
        message = json.dumps(json_data, default=json_datetime_default) 
        try:
            response = requests.post(f"https://{CARBONCHECK_SERVER_URL}/{WATER_USAGE_CLIENT}", headers=headers, data=message)
            result = response.json()
            result = result['success']
            for row in rows:
                usage_id = row[0]
                # update min, max _usage_id
                if min_usage_id is None or usage_id < min_usage_id:
                    min_usage_id = usage_id
                if max_usage_id is None or usage_id > max_usage_id:
                    max_usage_id = usage_id
            return result
        except Exception as e:
            return False
        


# 3. Log the range of the column you sent and the response you received from the server
def save_log(rows, result):
    for row in rows:
        message = str(row[1:])
        if result:
            logging.info(f"Sent {message} to the server")
        else:
            logging.error(f"Failed to send {message} to the server")


# 4. Read the log and decide whether to resend or not
def communication_result():
    pass

# service function for checking sent row number
def find_sent_range():
    with open("log/communication_log.txt", "r") as f:
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
    data = get_tuples()
    for i in range(0, len(data), BATCH_SIZE):
        rows = data[i:i+BATCH_SIZE]    # Slice the data by batch size
        result = send_data_to_server(rows) 
        print(result)
        save_log(rows,result)

    
    # 3. Log the range of the column you sent and the response you received from the server
    if min_usage_id is not None:
        logging.info(f"Sent rows with usage_id from {min_usage_id} to {max_usage_id} to the server")
    # 4. Read the log and decide whether to resend or not (or Try 5 mins later)
       



if __name__ == "__main__":
    main()

