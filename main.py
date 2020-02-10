from flask import Flask, request
from requests_oauthlib import OAuth1Session
import base64, hashlib, hmac
import json
import datetime
import config
from inference import inference
#import pprint

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
twitter = OAuth1Session(CK, CS, AT, ATS)

DM_ENDPOINT = 'https://api.twitter.com/1.1/direct_messages/events/new.json'
STATUS_UPDATE_ENDPOINT = 'https://api.twitter.com/1.1/statuses/update.json'
MYUSER_ID = '556940108'

app = Flask(__name__)

@app.route('/')
def hello_world():
    now_s = datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
    return '工事中…しばし待たれよ<br/><br/>{}'.format(now_s)

@app.route('/callback')
def callback():
    return 'OK', 200, {}

# Response a Challenge-Response Check Request
@app.route('/webhooks/twitter', methods = ['GET'])
def get():
    if 'crc_token' in request.args and len(request.args.get('crc_token')) == 48:
        crc_token = request.args.get('crc_token')
        sha256_hash_digest = hmac.new(CS.encode(), msg = crc_token.encode(), digestmod = hashlib.sha256).digest()

        response_token = 'sha256=' + base64.b64encode(sha256_hash_digest).decode()
        response = {'response_token': response_token}

        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    return 'No Content', 204, {'Content-Type': 'text/plain'}

@app.route('/webhooks/twitter', methods = ['POST'])
def get_webhook_event():
    data = request.data.decode('utf-8')
    data = json.loads(data)
    #pprint.pprint(data)

    # Process Tweet create events in order
    for tweet_create_event in data.get('tweet_create_events', []):
        # Look up for my id in the mentions
        first_flag = False
        for user_mention in tweet_create_event['entities']['user_mentions']:
            if user_mention['id_str'] == MYUSER_ID and first_flag == False:
                first_flag = True
                index_begin = user_mention['indices'][0]
                index_end = user_mention['indices'][1]
                sender_tweet_id = tweet_create_event['id_str']
                sender_screen_name = tweet_create_event['user']['screen_name']
                print('Sender screen_name:', sender_screen_name)

                # Get the text and delete first string of my screen_name(s)
                recieved_text = tweet_create_event['text']
                parsed_text = recieved_text[:index_begin] + recieved_text[index_end:]
                print('Text:', parsed_text)

                # Inference an idol through the input script
                result = inference(parsed_text)
                
                first_idol = next(iter(result))
                most_likelihood = round(result[first_idol] * 100, 2)
                candidate_str = ''
                for idol_name in result.keys():
                    candidate_str += '{} : {}%\n'.format(idol_name, str(round(result[idol_name] * 100, 2)))
                
                # Sending the result
                message = '{}ちゃん({}%)ですね！\n\nもしかしたら…\n{}'.format(first_idol, str(most_likelihood), candidate_str)
                print('To send text:', message)

                # Send a tweet
                params = {'status': message, 'in_reply_to_status_id': sender_tweet_id, 'auto_populate_reply_metadata': True}
                res = twitter.post(STATUS_UPDATE_ENDPOINT, params=params)
                print(res)

    # Process Direct Message events in order
    for dm_event in data.get('direct_message_events', []):
        recipient_user_id = dm_event['message_create']['target']['recipient_id']
        sender_id = dm_event['message_create']['sender_id']

        # Do nothing if the sender is same the recipient (Myself)
        if sender_id != MYUSER_ID:
            print('Sender id:', sender_id)
            # Get the text
            recieved_text = dm_event['message_create']['message_data']['text']
            print('Text:', recieved_text)

            # Inference an idol through the input script
            result = inference(recieved_text)
            
            first_idol = next(iter(result))
            most_likelihood = round(result[first_idol] * 100, 2)
            candidate_str = ''
            for idol_name in result.keys():
                candidate_str += '{} : {}%\n'.format(idol_name, str(round(result[idol_name] * 100, 2)))
            
            # Sending the result
            message = '{}ちゃん({}%)ですね！\n\nもしかしたら…:\n{}'.format(first_idol, str(most_likelihood), candidate_str)
            print('To send text:', message)

            # Send a Direct Message
            payload = {"event": {"type": "message_create", "message_create": {"target": {"recipient_id": sender_id}, "message_data": {"text": message}}}}
            
            res = twitter.post(DM_ENDPOINT, json=payload)
            print(res)
        else:
            print('Same user ID: ', recipient_user_id)
    
    return '', 200, {}

if __name__ == '__main__':
    app.run()