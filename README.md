# splitwise-csv [![Build Status](https://travis-ci.org/esecules/splitwise-csv.svg?branch=master)](https://travis-ci.org/esecules/splitwise-csv)
Upload expenses to splitwise from a csv file and splitting them evenly between a predefined group. 

##API Keys
You will need to obtain your own API keys from Splitwise.
https://secure.splitwise.com/apps/new
Set the "Callback URL" to "localhost:5000"
Store your consumer key and consumer secret in src/consumer_oauth.json like so:
```
{
    "consumer_key":"YOUR CONSUMER KEY",
    "consumer_secret":"YOUR CONSUMER SECRET"
}	
```

##Prerequesites
`pip install -r setup/requirements.txt`

##Usage
###First Usage
`python groupsplit.py <transactions csv> <splitwise group name>`
You will need a Display to authorize this application by entering your login information in the browser spawned from here.
It will ask you a few questions to determine which columns have the date, amount and description, etc. You can save the answers for future use. Then you go through each transaction one by one marking them to be split (or not). Finally it uploads them to your splitwise.
###Normal Usage
`python groupsplit.py <transactions csv> <splitwise group name>`
It will skip right to going through your transactions one by one, so long as you have agreed to it remembering your csv layout. It will also remember the last transaction you considered and start from the one which follows it.
##Resetting
Just delete any or all of the .pkl (pickeled) files. 
If you start to use a new csv layout you have to delete the csv_settings.pkl file 
