import os
import csv
import sys
import json
import pickle
import pprint
import urllib
import requests
import subprocess
import webbrowser
import oauthlib.oauth1
from money import Money
from pprint import pprint
from datetime import datetime

def get_client_auth():
    if os.path.isfile("consumer_oauth.json"):
        with open("consumer_oauth.json", 'rb') as oauth_file:
            consumer = json.load(oauth_file)
            ckey = consumer['consumer_key']
            csecret = consumer['consumer_secret']
    else:
        with open("consumer_oauth.json", 'wb') as oauth_file:
            json.dump({'consumer_key':'YOUR KEY HERE',
                       'consumer_secret':'YOUR SECRET HERE'}, oauth_file)
        exit("go to https://secure.splitwise.com/oauth_clients to obtain your keys."+
             "place them in consumer_oauth.json")
    return ckey, csecret

def get_client():
    ckey, csecret = get_client_auth()
    client = oauthlib.oauth1.Client(ckey, client_secret=csecret)
    uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_request_token",
                                     http_method='POST')
    r = requests.post(uri, headers=headers, data=body)
    resp = r.text.split('&')
    oauth_token = resp[0].split('=')[1]
    oauth_secret = resp[1].split('=')[1]
    uri = "https://secure.splitwise.com/authorize?oauth_token=%s" % oauth_token

    webbrowser.open_new(uri)

    proc = subprocess.Popen(['./server.py'], stdout=subprocess.PIPE, shell=True)
    stdout, stderr = proc.communicate()
    if stderr:
        exit(stderr)
    client = oauthlib.oauth1.Client(ckey, client_secret=csecret,
                                    resource_owner_key=oauth_token,
                                    resource_owner_secret=oauth_secret,
                                    verifier=stdout.strip())

    uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_access_token",
                                     http_method='POST')
    resp = requests.post(uri, headers=headers, data=body)
    tokens = resp.text.split('&')
    oauth_token = tokens[0].split('=')[1]
    oauth_secret = tokens[1].split('=')[1]
    client = oauthlib.oauth1.Client(ckey, client_secret=csecret,
                                    resource_owner_key=oauth_token,
                                    resource_owner_secret=oauth_secret,
                                    verifier=stdout.strip())
    with open('oauth_client.pkl', 'wb') as pkl:
        pickle.dump(client, pkl)
    return client

def split(total, num_people):
    base = total * 100 // num_people / 100
    extra = total - num_people * base
    assert base * num_people + extra == total, "InternalError:" + \
    " something doesnt add up here: %d * %d + %d != %d" %(base, num_people, extra, total)
    return base, extra

def api_call(url, http_method, client):
    uri, headers, body = client.sign(url, http_method=http_method)
    resp = requests.request(http_method, uri, headers=headers, data=body)
    return resp.json()

def main():
    if os.path.isfile("oauth_client.pkl"):
        with open('oauth_client.pkl', 'rb') as oauth_pkl:
            client = pickle.load(oauth_pkl)
    else:
        client = get_client()

    resp = api_call("https://secure.splitwise.com/api/v3.0/get_current_user", 'GET', client)
    my_id = resp['user']['id']

    resp = api_call("https://secure.splitwise.com/api/v3.0/get_groups", 'GET', client)
    num_found = 0
    gid = ''
    members = {}

    for group in resp['groups']:
        if group['name'].lower() == sys.argv[2].lower():
            gid = group['id']
            members = [m['id'] for m in group['members'] if m['id'] != my_id]
            num_found += 1

    if num_found > 1:
        exit("More than 1 group found")
    elif num_found < 1:
        exit("No matching group")
    elif len(members) < 1:
        exit("No members in group")

    with open(sys.argv[1], 'rb') as csvfile:
        reader = csv.reader(csvfile)
        rows = [x for x in reader]


    if os.path.isfile("csv_settings.pkl"):
        with open('csv_settings.pkl', 'rb') as f:
            date_col, amount_col, desc_col, has_title_row, local_currency, remember = pickle.load(f)

    else:
        print "These are the first two rows of your csv"
        print '\n'.join([str(t) for t in rows[0:2]])
        print 'Colnum numbers start at 0'
        date_col = input("Which column has the date?")
        amount_col = input("Which column has the amount?")
        desc_col = input("Which column has the description?")
        has_title_row = raw_input("Does first row have titles? [Y/n]").lower() != 'n'
        local_currency = raw_input("What currency were these transactions made in?")
        test = Money("1.00", local_currency)  #pylint: disable=W0612
        remember = raw_input("Remember these settings? [Y/n]").lower() != 'n'

    if remember:
        with open("csv_settings.pkl", "wb") as pkl:
            csv_settings = (date_col, amount_col, desc_col, has_title_row, local_currency, remember)
            pickle.dump(csv_settings, pkl)

    if has_title_row:
        rows = rows[1:]
    transactions = [{"date":datetime.strftime(datetime.strptime(r[date_col], "%m/%d/%y"), "%Y-%m-%dT%H:%M:%SZ"),
                     "amount":-1 * Money(r[amount_col], local_currency),
                     "desc":r[desc_col]}
                    for r in rows if float(r[amount_col]) < 0]
    splits = []
    for t in transactions:
        if raw_input("%s at %s $%s. Split? [y/N]" % (t['date'], t['desc'], t['amount'])).lower() == 'y':
            splits.append(t)


    print "Uploading %d splits" % len(splits)
    one_cent = Money("0.01", local_currency)
    for s in splits:
        num_people = len(members) + 1
        base, extra = split(s['amount'], num_people)
        params = {
            "payment": 'false',
            "cost": s["amount"].amount,
            "description": s["desc"],
            "date": s["date"],
            "group_id": gid,
            "currency_code": local_currency,
            "users__0__user_id": my_id,
            "users__0__paid_share": s["amount"].amount,
            "users__0__owed_share": base.amount,
        }
        for i in range(len(members)):
            params['users__%s__user_id' % (i+1)] = members[i]
            params['users__%s__paid_share' % (i+1)] = 0
            params['users__%s__owed_share' % (i+1)] = (base + one_cent).amount if extra else base.amount
            extra -= one_cent
        paramsStr = urllib.urlencode(params)
        uri = "https://secure.splitwise.com/api/v3.0/create_expense?%s" % (paramsStr)
        resp = api_call(uri, 'POST', client)
        if resp["errors"]:
            print "URI:"
            print uri
            pprint(resp)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
