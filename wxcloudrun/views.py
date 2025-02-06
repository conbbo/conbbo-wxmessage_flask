from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters, Users
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import requests
import json
import xml.etree.ElementTree as ET
from wxcloudrun import db


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/getqr', methods=['GET'])
def get_qr():
    """
    获取临时二维码
    :return: 二维码ticket和url
    """
    try:
        # 获取access_token (微信云托管环境下自动鉴权)
        app_id = 'wx580dad6261cf35c6'
        token_url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}'
        token_response = requests.get(token_url)
        access_token = token_response.json().get('access_token')

        if not access_token:
            error_info = {
                'status_code': token_response.status_code,
                'headers': dict(token_response.headers),
                'response': token_response.json()
            }
            return make_err_response(f'获取access_token失败，详细信息：{json.dumps(error_info, ensure_ascii=False)}')

        # 生成临时二维码
        qr_url = f'https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}'
        qr_data = {
            'expire_seconds': 2592000,  # 30天有效期
            'action_name': 'QR_STR_SCENE',
            'action_info': {
                'scene': {
                    'scene_str': 'test'
                }
            }
        }
        qr_response = requests.post(qr_url, json=qr_data)
        qr_result = qr_response.json()

        if 'ticket' not in qr_result:
            return make_err_response('生成二维码失败')

        # 返回二维码信息
        return make_succ_response({
            'ticket': qr_result['ticket'],
            'url': qr_result['url']
        })

    except Exception as e:
        return make_err_response(f'获取二维码失败: {str(e)}')


@app.route('/api/wx/event', methods=['POST'])
def handle_wx_event():
    """
    处理微信事件推送
    :return: 返回success的响应
    """
    try:
        # 解析XML消息
        xml_data = request.data
        root = ET.fromstring(xml_data)
        
        # 获取消息类型
        msg_type = root.find('MsgType').text
        if msg_type != 'event':
            return 'success'
            
        # 获取事件类型
        event = root.find('Event').text
        if event != 'subscribe':
            return 'success'
            
        # 获取用户openid
        openid = root.find('FromUserName').text
        
        # 获取场景值
        event_key = root.find('EventKey')
        scene_str = 'default'
        if event_key is not None:
            # EventKey格式为：qrscene_xxx，需要去掉前缀
            scene_str = event_key.text.replace('qrscene_', '') if event_key.text else 'default'
        
        # 保存用户信息
        user = Users()
        user.openid = openid
        user.type = scene_str
        user.stime = datetime.now()
        db.session.add(user)
        db.session.commit()
        
        return 'success'
        
    except Exception as e:
        # 记录错误但返回success，避免微信服务器重试
        print(f'处理微信事件失败: {str(e)}')
        return 'success'
