#!/usr/bin/env python3

import argparse
import requests
import json
from datetime import date, timedelta

OK = ['IN_QUEUE', 'ACTIVE', 'SUCCESSFUL', 'INFO',  'TIMING', 'INITIALISATION', 'UNUSED', 'WAITING']
WARNING = ['CANCELLED', 'PARTIALLY_DELETED', 'DELETED']
CRITICAL = ['ERROR', 'SUPPRESSED']
UNKOWN = ['NONE']
exit_code = 0

def set_exit_code(code):
    global exit_code
    if code > exit_code:
        exit_code = code

def get_status():
    if exit_code == 0:
        return 'OK'
    elif exit_code == 1:
        return 'WARNING'
    elif exit_code == 2:
        return 'CRITICAL'
    else:
        return 'UNKNOWN'

def set_status(status):
    if status in OK:
        set_exit_code(0)
    elif status in CRITICAL:
        set_exit_code(2)
    elif status in WARNING:
        set_exit_code(1)
    else:
        set_exit_code(3)

def main():
    parser = argparse.ArgumentParser(description='Monitoring check for SEP Sesam migrationq states')
    parser.add_argument('--user',
                        '-u',
                        required=True,
                        type=str,
                        help='Username for the sesam REST API',
                        dest='user')
    parser.add_argument('--password',
                        '-p',
                        required=True,
                        type=str,
                        help='Password to the given username',
                        dest='password')
    parser.add_argument('--hostname',
                        '-H',
                        required=True,
                        type=str,
                        help='Host name argument for sesam server',
                        dest='hostname',
                        metavar='<IP or URI>')
    parser.add_argument('--port',
                        '-P',
                        required=False,
                        help='Port number of sesam service',
                        dest='port',
                        default='11401')
    # get the arguments
    args = parser.parse_args()
    # Expected output: ["username","hunter2"]
    payload = ("[" + '"' + str(args.user) + '"' +"," + '"' + str(args.password) + '"' + "]")

    # get auth token from server
    try:
        token = requests.post('http://' + args.hostname + ':' + args.port + '/sep/api/server/login', data=payload)
    except requests.ConnectionError:
        print("Sesam API is not reachable")
        exit(3)
    else:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Sesam-Dateformat': 'yyyy-MM-dd HH:mm:ss',
            'X-SEP-Session': token.text
        }

        # Get results from yeasterday in JSON
        backup_results = requests.post('http://' + args.hostname + ':' + args.port + '/sep/api/migrationResults/filter', json={"sesamDate": [ str(date.today() - timedelta(days=1))]}, headers=headers)
        content = json.loads(backup_results.text)

        # get state array
        item_state = []
        for i in content:
            item_state.append(i['state'])

        # get name array
        item_name = []
        for i in content:
            item_name.append(i['task']['name'])

        # get mtime array
        item_mtime = []
        for i in content:
            item_mtime.append(i['mtime'])

        # get comment
        item_comment = []
        for i in content:
            try:
                item_comment.append(i['sepcomment'])
            except:
                item_comment.append("no sepcomment for this Job. Please check backup logs")
         # shell output
        for i in range(len(item_state)):
            print(item_state[i] + " " + item_name[i] + " " + item_mtime[i] + "      " + item_comment[i])
            set_status(item_state[i])

        exit(exit_code)

if __name__ == '__main__':
    main()
