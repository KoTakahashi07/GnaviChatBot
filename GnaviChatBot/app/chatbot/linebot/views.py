from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import AssistantV2
from linebot.models import ChatBotSession
from django.utils import timezone
import requests
import json

def send_line_messages(session, reply_token, messages):
    """
    メッセージをLINEに送信
    """
    if type(messages) is not list:
        messages = [messages]
    parsed_messages = [
        {'type':'text','text':message} if type(message) is str else message for message in messages]
    
    payload = {
        "replyToken": reply_token,
        "messages": parsed_messages
    }
    result = requests.post(
        settings.LINE_SETTINGS['REPLY_ENDPOINT'],
        headers=settings.LINE_SETTINGS['HEADER'],
        data=json.dumps(payload)
        )
    return result
 
def parse_line_messages(request_json):
    """
    LINEからのメッセージをパース
    """
    for event in request_json['events']:
        reply_token = event['replyToken']  # 返信先トークンの取得
        message_type = event['message']['type']   # typeの取得
        user_id = event['source']['userId'] # user id
        if message_type == 'text':
            # エリアと店名を分割する
            splited_txt = event['message']['text'].split('、')
            area = splited_txt[0]
            food_type = splited_txt[1]
        
    return reply_token, area, food_type, user_id
 
def session_process(user_id):
    """
    セッションの作成及び無効化
    """
    session, _ = ChatBotSession.objects.get_or_create(user_id=user_id)
    if not session.check_session():
        session.expire_time = session.update_expire_time()
        session.watson_session = ''
        session.current_logic = ''
        session.save()
    return session

from django.conf import settings
def watson_assistant(session, text):
    """
    Watson Assistantにリクエスト送信
    """
    # 初期設定
    authenticator = IAMAuthenticator(settings.WATSON_SETTINGS['API_KEY'])
    assistant = AssistantV2(
        version=settings.WATSON_SETTINGS['VERSION'],
        authenticator=authenticator
        )
    assistant.set_service_url(settings.WATSON_SETTINGS['URL'])
    # Watsonのセッション取得
    response_session_id = assistant.create_session(
    assistant_id=settings.WATSON_SETTINGS['ASSISTANT_ID']
    ).get_result()
    watson_session = response_session_id['session_id']
 
    # リクエスト送信
    response = assistant.message(
        assistant_id=settings.WATSON_SETTINGS['ASSISTANT_ID'],
        session_id=watson_session,
        input={'message_type': 'text', 'text': text}
        ).get_result()
    returned_text = response['output']['generic'][0]['text']

    return returned_text

def create_test_message(result_api):
    """
    カルーセル表示のテストメッセージを作成する。
    """
    rest_name_list = []
    rest_address_list = []
    rest_latitude_list = []
    rest_longitude_list = []
    rest_url_mobile_list = []
    rest_image_list = []
    rest_pr_list = []
    rest_tel_list = []

    for i in range(3):
        # print(result_api['rest'][i]['address'])
        # print(result_api['rest'][i]['name'])
        # print(result_api['rest'][i]['code']['areaname'])
        # print(result_api['rest'][i]['category'])
        # print('----------------------------------------------------')
        rest_name_list.append(result_api['rest'][i]['name'])
        rest_address_list.append(result_api['rest'][i]['address'])
        rest_latitude_list.append(result_api['rest'][i]['latitude'])
        rest_longitude_list.append(result_api['rest'][i]['longitude'])
        rest_url_mobile_list.append(result_api['rest'][i]['url_mobile'])
        rest_image_list.append(result_api['rest'][i]['image_url'])
        rest_pr_list.append(result_api['rest'][i]['pr'])
        rest_tel_list.append(result_api['rest'][i]['tel'])
    # 文字数制限。これしないと文字数超過になる。
    pr1 = rest_pr_list[0]['pr_short'][0:20]
    pr2 = rest_pr_list[1]['pr_short'][0:20]
    pr3 = rest_pr_list[2]['pr_short'][0:20]
    # Mapアドレスに緯度と経度を入れる。
    map_address1 = \
        f"https://www.google.co.jp/maps/@{rest_latitude_list[0]},{rest_longitude_list[0]},17z?hl=ja"
    map_address2 = \
        f"https://www.google.co.jp/maps/@{rest_latitude_list[1]},{rest_longitude_list[1]},17z?hl=ja"
    map_address3 = \
        f"https://www.google.co.jp/maps/@{rest_latitude_list[2]},{rest_longitude_list[2]},17z?hl=ja"    
    
    message = {
        "type": "template",
        "altText": "this is a carousel template",
        "template": {
            "type": "carousel",
            "actions": [],
            "columns": [
            {   
            "thumbnailImageUrl": rest_image_list[0]['shop_image1'],
            "title": rest_name_list[0],
            "text": pr1,
            "actions": [
            {
                "type": "uri",
                "label": "URL",
                "uri": rest_url_mobile_list[0]
            },
            {
                "type": "uri",
                "label": "MAP",
                "uri": map_address1
            },
            {
                "type": "message",
                "label": "TEL",
                "text": rest_tel_list[0]
            }
                ]
            },
            {
                "thumbnailImageUrl": rest_image_list[1]['shop_image1'],
                "title": rest_name_list[1],
                "text": pr2,
                "actions": [
                {
                    "type": "uri",
                "label": "URL",
                "uri": rest_url_mobile_list[1]
                },
                {
                    "type": "uri",
                    "label": "MAP",
                    "uri": map_address2
                },
                {
                    "type": "message",
                    "label": "TEL",
                    "text": rest_tel_list[1]
                }
                ]
            },
            {
                "thumbnailImageUrl": rest_image_list[2]['shop_image1'],
                "title": rest_name_list[2],
                "text": pr3,
                "actions": [
                {
                    "type": "uri",
                "label": "URL",
                "uri": rest_url_mobile_list[2]
                },
                {
                    "type": "uri",
                    "label": "MAP",
                    "uri": map_address3
                },
                {
                    "type": "message",
                    "label": "TEL",
                    "text": rest_tel_list[2]
                }
                ]
            }
            ]}
        }
    return message

def gurunabi_api(area, shop_name):
    """
    フードのリクエストに合わせてお店を提案。
    """
    url = 'https://api.gnavi.co.jp/RestSearchAPI/v3/'

    #パラメータの設定
    params={}
    params["keyid"] = "1dd223c2b5cc05ea614281cc405dccce" #取得したアクセスキー
    params["freeword"] = shop_name
    params['address'] = area
    
    result_api = requests.get(url, params=params).json()
    message = create_test_message(result_api)
    
    return message

def create_gurunabi_message(area, shop_name):

    message = gurunabi_api(area, shop_name)

    return message

@csrf_exempt
def callback(request):
    """
    コールバック送信
    """
    request_json = json.loads(request.body.decode('utf-8')) # requestの情報をdict形式で取得
    
    token, area, food_type, user_id = parse_line_messages(request_json) # 受信したメッセージをパース
    # message = f'「{text}」と送信しました'
    session = session_process(user_id)
    # print('next_logic', type(session.next_logic))
    # message = watson_assistant(session, text) # Watson Assistantに送信
    # messages = [message] # このmessageはwatosonからの返信
    # print('messages', messages)
    watson_result = watson_assistant(session, food_type)

    if watson_result == 'RESTAURANT_ASK_LOGIC':

        message = create_gurunabi_message(area, food_type)

    send_line_messages(session, token, message)   # LINEにセリフを送信する関数

    return HttpResponse("This is bot api.")

def index(request):
    return HttpResponse("This is bot api.")
