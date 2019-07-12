from flask import Flask, request, jsonify, render_template
import os
import dialogflow
import requests
import json

import datetime
import pytz
import bisect
import numpy as np

import sys
import logging

# Log to both console + file
logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt = '%Y-%m-%d %H:%M:%S',
                    handlers = [
	                    logging.FileHandler('bus_va.log', 'w', 'utf-8'),
	                    logging.StreamHandler(sys.stdout)
                    ])

log = logging.getLogger()

# API KEY: AIzaSyA-jCTd8D71o-QmHknw8o1T-HAgEr_SF4I
app = Flask(__name__)

@app.route('/')
def index():
    log.debug('index()')
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    log.debug('webhook()')
    data = request.get_json(silent=True)   # get the incoming JSON structure
    action = data['queryResult']['action'] # get the action name associated with the matched intent

    if (action == 'get_pickup'):
        return get_pickup(data)

def utc_2_local():
    now_utc = datetime.datetime.now()
    local_tz = pytz.timezone('Asia/Singapore')
    local_dt = now_utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return (local_dt)

def get_pickup(data):
    log.debug('get_pickup()')
    property = data['queryResult']['parameters']['property']
    log.debug("PROPERTY --> " + property)

    pickup = data['queryResult']['parameters']['pickupPoint']
    log.debug("PICKUP --> " + pickup)

    # now = datetime.datetime.now()    ### gets the current time
    # dayofweek = now.weekday()   # 0 - 4 is weekday ; 5-6 is weekend
    now = utc_2_local()
    dayofweek = now.weekday()

    log.debug('HOUR: ' + str(now.hour) + ' MINUTE: ' + str(now.minute))

    if (dayofweek > 4 )  :
          daytype = "Weekend"
    else:
          daytype = "Weekday"

    log.debug('DAY of WEEK: ' + str(dayofweek))
    scheduleTimings = get_shuttleschedule(property, pickup, daytype, now)

    log.debug('Shuttle Schedule Timings: ' + str(scheduleTimings))
    #do_processTimes(scheduleTimings, now.time())

    response = "Pickup times for " + property + " from " + pickup + " are as follows: " + str(scheduleTimings)
    log.debug('RESPONSE: ' + response)

    reply = {}
    reply["fulfillmentText"] = ""
    reply["fulfillmentMessages"] = []


    ### TODO #5: Creates the message object for Telegram
    ### .
    msg_object = {}
    msg_object["platform"] = "TELEGRAM"

    ### TODO #6: Creates the custom payload with inline_keyboard
    msg_object["payload"] = {}
    msg_object["payload"]["telegram"] = {}
    msg_object["payload"]["telegram"]["text"] = response
    msg_object["payload"]["telegram"]["reply_markup"] = {}
    msg_object["payload"]["telegram"]["reply_markup"]["inline_keyboard"] = []

    ### TODO #7: Creates a keyboard row with two keys and append to the message object
    tg_keyboard_row = []
    tg_keyboard_row.append({"text" : "👍👍", "callback_data" : "thanks for the information"})
    tg_keyboard_row.append({"text" : "😊😊", "callback_data" : "appreciate your fast response"})

    msg_object["payload"]["telegram"]["reply_markup"]["inline_keyboard"].append(tg_keyboard_row)

    reply["fulfillmentMessages"].append(msg_object)

    log.debug("REPLY: " + str(reply))

    log.debug("JSONIFY REPLY: " + str(jsonify(reply)))
    return jsonify(reply)

# timingList - array of strings
# target - current time as string
def do_processTimes(timingList, target):
    log.debug('do_processTimes(): ' + str(timingList) + ' Target: ' +  str(target))

    ind = 0
    # Ref: https://stackoverflow.com/questions/1614236/in-python-how-do-i-convert-all-of-the-items-in-a-list-to-floats
    if len(timingList) > 1:
        timingList2Float = np.array(np.array(timingList, dtype=float))
        ind = bisect.bisect_left(timingList2Float, float(target))

        if ind < 0 or ind >= len(timingList):
            # return ['No Service']
            return "No Service"
        return (timingList[ind])
    else:
		# return [timingList[ind]]
        return timingList[ind]

def get_shuttleschedule(property, pickup_point, day_type, currentTime):
## Route a dictionary containing tuples as the key.
## Each tuple refers a unique combination of property, pickup point, weekdaytype. 
## Based on the tuple combination, there will be a list containing the leaving time.
## This list is returned by the function
## The dictionary below represents the hypothetical bus schedule from 
    routes = {
                 ("Goodlife Club", "Clubhouse", "Weekday"): ["13.00", "15.00", "17.00", "19.00"],
                 ("Goodlife Club", "Pasir Ris MRT", "Weekday"): ["13.30", "15.30", "17.30", "19.30"],
                 ("Goodlife Club", "Clubhouse", "Weekend"): ["13.00", "14.00", "15.00", "16.00", "17.00", "18.00","19.00"],
                 ("Goodlife Club", "Pasir Ris MRT", "Weekend"): ["13.30", "14.30","15.30", "16.30", "17.30", "18.30","19.30"],
                 ("AI Hub Park", "Clementi MRT", "Weekday"): ["8.00", "8.30", "9.00"],
                 ("AI Hub Park", "Clementi MRT", "Weekend"): ["No services"],
                 ("AI Hub Park", "Block A", "Weekday"): ["17.00", "18.00", "19.00"],
                 ("AI Hub Park", "Block B", "Weekday"): ["17.15", "18.15", "19.15"],
                 ("AI Hub Park", "Block A", "Weekend"): ["No services"],
                 ("AI Hub Park", "Block B", "Weekend"): ["No services"],
                }
    log.debug('get_shuttleschedule: property = ' + property + ' ' + ' pickup_point = ' + pickup_point + ' day_type = ' + day_type)
    timingsList = routes.get( (property,  pickup_point , day_type ), ["There is no route found"])

    log.debug('get_shuttleschedule: ' + str(timingsList))
    result = do_processTimes(timingsList, currentTime.strftime('%H.%M'))

    log.debug('Time to board: ' + result)
    return result

if __name__ == "__main__":
    # Web Service
    app.run()
	
