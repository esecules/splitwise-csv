#! /usr/bin/python

import requests
import csv
import sys
import oauthlib.oauth1
import pprint
import webbrowser
import subprocess
import os
import pickle
import json
import urllib
from pprint import pprint
from datetime import datetime

if os.path.isfile("consumer_oauth.json"):
    with open("consumer_oauth.json", 'rb') as f:
        consumer = json.load(f)
        ckey=consumer['consumer_key']
        csecret = consumer['consumer_secret']
else:
    with open("consumer_oauth.json", 'wb') as f:
        json.dump({'consumer_key':'YOUR KEY HERE',
                   'consumer_secret':'YOUR SECRET HERE'}, f)
    exit("go to https://secure.splitwise.com/oauth_clients to obtain your keys. place them in consumer_oauth.json")

def get_client():
    client = oauthlib.oauth1.Client( ckey, client_secret=csecret )
    uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_request_token", http_method='POST')
    r = requests.post(uri, headers=headers, data=body)
    resp = r.text.split('&')
    oauth_token = resp[0].split('=')[1]
    oauth_secret = resp[1].split('=')[1]
    uri = "https://secure.splitwise.com/authorize?oauth_token=%s" % oauth_token

    webbrowser.open_new(uri)

    p = subprocess.Popen(['./server.py'], stdout=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    client = oauthlib.oauth1.Client(ckey, client_secret=csecret,
                                    resource_owner_key=oauth_token, resource_owner_secret=oauth_secret,
                                    verifier=stdout.strip())

    uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_access_token", http_method='POST')
    r = requests.post(uri, headers=headers, data=body)
    resp = r.text.split('&')
    oauth_token = resp[0].split('=')[1]
    oauth_secret = resp[1].split('=')[1]
    client = oauthlib.oauth1.Client(ckey, client_secret=csecret,
                                    resource_owner_key=oauth_token, resource_owner_secret=oauth_secret,
                                    verifier=stdout.strip())
    with open('oauth_client.pkl', 'wb') as f:
        pickle.dump(client, f)
    return client


if os.path.isfile("oauth_client.pkl"):
    with open('oauth_client.pkl', 'rb') as f:
        client = pickle.load(f)
else:
    client = get_client()

#uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_expenses?limit=3", http_method='GET')
#r = requests.get(uri, headers=headers, data=body)
#r = json.loads(r.text)

uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_current_user", http_method='GET')
r = requests.get(uri, headers=headers, data=body)
r = json.loads(r.text)
myId = r['user']['id']

uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_groups", http_method='GET')
r = requests.get(uri, headers=headers, data=body)
r = json.loads(r.text)
numFound = 0
gid=''
members={}
for group in r['groups']:
    if group['name'].lower() == sys.argv[2].lower():
        gid = group['id']
        members=[ m['id'] for m in group['members'] if m['id'] != myId ]
        numFound += 1

print members

if numFound > 1:
    exit("More than 1 group found")
elif numFound < 1:
    exit("No matching group")
elif len( members ) < 1:
    exit("No members in group")
with open(sys.argv[1], 'rb') as csvfile:
    reader = csv.reader(csvfile)
    rows = [ x for x in reader ]


print "These are the first two rows of your csv"
print '\n'.join( [ str(t) for t in rows[0:2] ] )
print 'Colnum numbers start at 0'
dateCol = input("Which column has the date?")
amountCol = input("Which column has the amount?")
descCol = input("Which column has the description?")
titleRow = raw_input("Does first row have titles? [Y/n]").lower() != 'n'
if titleRow:
    rows = rows[1:]
transactions = [ {    "date":datetime.strftime(datetime.strptime(r[dateCol],"%m/%d/%y"), "%Y-%m-%dT%H:%M:%SZ"),
                      "amount":-1 * float(r[amountCol]),
                      "desc":r[descCol] }
                 for r in rows if float(r[amountCol]) < 0 ]
splits = []
for t in transactions:
    if raw_input("%s at %s $%s. Split? [y/N]" % (t['date'], t['desc'], t['amount'])).lower() == 'y':
        splits.append(t)



for s in splits:
    numPeople=len(members) + 1
    totalCents = int(s['amount'] * 100)
    baseAmount = totalCents // numPeople
    extraCents = totalCents - numPeople * baseAmount
    params = {
        "payment": 'false',
        "cost": s["amount"],
        "description": s["desc"],
        "date": s["date"],
        "group_id":gid,
        "users__0__user_id":myId,
        "users__0__paid_share":s["amount"],
        "users__0__owed_share":baseAmount/100.0,
    }
    for i in range(len(members)):
        params['users__%s__user_id' % (i+1)] = members[i]
        params['users__%s__paid_share' % (i+1)] = 0
        params['users__%s__owed_share' % (i+1)] = (baseAmount + 1)/100.0 if extraCents else baseAmount/100.0
        extraCents-=1
    params = urllib.urlencode(params)
    uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/create_expense?%s" % params, http_method='POST')
    print "Request"
    print uri
    print "Headers:"
    print headers
    print "Body:"
    print body
    r = requests.post(uri, headers=headers, data=params)
    resp = json.loads(r.text)
    print "Response:"
    pprint(resp)
