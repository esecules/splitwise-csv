import os
import re
import csv
import sys
import json
import pickle
import pprint
import urllib
import optparse
import requests
import subprocess
import webbrowser
import oauthlib.oauth1
from money import Money
from pprint import pprint
from datetime import datetime

def split(total, num_people):
    base = total * 100 // num_people / 100
    extra = total - num_people * base
    assert base * num_people + extra == total, "InternalError:" + \
    " something doesnt add up here: %d * %d + %d != %d" %(base, num_people, extra, total)
    return base, extra

class Splitwise:
    def __init__(self):
        if os.path.isfile("oauth_client.pkl"):
            with open('oauth_client.pkl', 'rb') as oauth_pkl:
                self.client = pickle.load(oauth_pkl)
        else:
            self.get_client()
        
    def get_client_auth(self):
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
        self.ckey = ckey
        self.csecret = csecret
        
    def get_client(self):
        self.get_client_auth()
        client = oauthlib.oauth1.Client(self.ckey, client_secret=self.csecret)
        uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_request_token",
                                         http_method='POST')
        r = requests.post(uri, headers=headers, data=body)
        resp = r.text.split('&')
        oauth_token = resp[0].split('=')[1]
        oauth_secret = resp[1].split('=')[1]
        uri = "https://secure.splitwise.com/authorize?oauth_token=%s" % oauth_token
    
        webbrowser.open_new(uri)
    
        proc = subprocess.Popen(['python', 'server.py'], stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if stderr:
            exit(stderr)
        client = oauthlib.oauth1.Client(self.ckey, client_secret=self.csecret,
                                        resource_owner_key=oauth_token,
                                        resource_owner_secret=oauth_secret,
                                        verifier=stdout.strip())
    
        uri, headers, body = client.sign("https://secure.splitwise.com/api/v3.0/get_access_token",
                                         http_method='POST')
        resp = requests.post(uri, headers=headers, data=body)
        tokens = resp.text.split('&')
        oauth_token = tokens[0].split('=')[1]
        oauth_secret = tokens[1].split('=')[1]
        client = oauthlib.oauth1.Client(self.ckey, client_secret=self.csecret,
                                        resource_owner_key=oauth_token,
                                        resource_owner_secret=oauth_secret,
                                        verifier=stdout.strip())
        with open('oauth_client.pkl', 'wb') as pkl:
            pickle.dump(client, pkl)
        self.client = client
    
    def api_call(self, url, http_method):
        uri, headers, body = self.client.sign(url, http_method=http_method)
        resp = requests.request(http_method, uri, headers=headers, data=body)
        return resp.json()

    def get_id(self):
        if not hasattr(self, "my_id"):
            resp = self.api_call("https://secure.splitwise.com/api/v3.0/get_current_user", 'GET')
            self.my_id = resp['user']['id']
        return self.my_id

    def get_groups(self):
        resp = self.api_call("https://secure.splitwise.com/api/v3.0/get_groups", 'GET')
        return resp['groups']

    def post_expense(self, uri):
        resp = self.api_call(uri, 'POST')
        if resp["errors"]:
            print "URI:"
            print uri
            pprint(resp)
        else:
            sys.stdout.write(".")
            sys.stdout.flush()

class SplitGenerator():
    def __init__(self, options, args, api):
        self.api = api
        csv_file = args[0]
        group_name = args[1]
        with open(csv_file, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            self.rows = [x for x in reader]
    
    
        if os.path.isfile("csv_settings.pkl"):
            with open('csv_settings.pkl', 'rb') as f:
                self = pickle.load(f)
    
        else:
            print "These are the first two rows of your csv"
            print '\n'.join([str(t) for t in self.rows[0:2]])
            print 'Colnum numbers start at 0'
            self.date_col = input("Which column has the date?")
            self.amount_col = input("Which column has the amount?")
            self.desc_col = input("Which column has the description?")
            self.has_title_row = raw_input("Does first row have titles? [Y/n]").lower() != 'n'
            self.local_currency = raw_input("What currency were these transactions made in?").upper()
            self.test = Money("1.00", self.local_currency)  #pylint: disable=W0612
            self.remember = raw_input("Remember these settings? [Y/n]").lower() != 'n'
    
        if self.remember:
            with open("csv_settings.pkl", "wb") as pkl:
                pickle.dump(self, pkl)
    
        if self.has_title_row:
            self.rows = self.rows[1:]
            
        self.make_transactions()
        self.get_group(group_name)
        self.splits = []
        self.ask_for_splits()
        
    def make_transactions(self):
        self.transactions = [{"date": datetime.strftime(datetime.strptime(r[self.date_col], "%m/%d/%y"), "%Y-%m-%dT%H:%M:%SZ"),
                              "amount": -1 * Money(r[self.amount_col], self.local_currency),
                              "desc": re.sub('\s+',' ', r[self.desc_col])}
                             for r in self.rows if float(r[self.amount_col]) < 0]

    def get_group(self, name):
        num_found = 0
        gid = ''
        members = {}
        groups = self.api.get_groups()
        for group in groups:
            if group['name'].lower() == name.lower():
                gid = group['id']
                members = [m['id'] for m in group['members'] if m['id'] != self.api.get_id()]
                num_found += 1
    
        if num_found > 1:
            exit("More than 1 group found")
        elif num_found < 1:
            exit("No matching group")
        elif len(members) < 1:
            exit("No members in group")

        self.members = members
        self.gid = gid
        
    def ask_for_splits(self):
        for t in self.transactions:
            if raw_input("%s at %s $%s. Split? [y/N]" % (t['date'], t['desc'], t['amount'])).lower() == 'y':
                self.splits.append(t)

    def __getitem__(self, index):
        s = self.splits[index]
        one_cent = Money("0.01", self.local_currency)
        num_people = len(self.members) + 1
        base, extra = split(s['amount'], num_people)
        params = {
            "payment": 'false',
            "cost": s["amount"].amount,
            "description": s["desc"],
            "date": s["date"],
            "group_id": self.gid,
            "currency_code": self.local_currency,
            "users__0__user_id": self.api.get_id(),
            "users__0__paid_share": s["amount"].amount,
            "users__0__owed_share": base.amount,
        }
        for i in range(len(self.members)):
            params['users__%s__user_id' % (i+1)] = sef.members[i]
            params['users__%s__paid_share' % (i+1)] = 0
            params['users__%s__owed_share' % (i+1)] = (base + one_cent).amount if extra else base.amount
            extra -= one_cent
        paramsStr = urllib.urlencode(params)
        return "https://secure.splitwise.com/api/v3.0/create_expense?%s" % (paramsStr)
        
        
def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose', default=False, dest='verbose')
    options, args = parser.parse_args()
    splitwise = Splitwise()
    split_gen = SplitGenerator(options, args, splitwise)
    print "Uploading splits"
    for uri in split_gen:
        splitwise.post_expense(uri)
    sys.stdout.write("\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
