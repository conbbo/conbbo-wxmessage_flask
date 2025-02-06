from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import requests
import json


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
            return make_err_response('获取access_token失败')

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
            'url': qr_result['url'
        })

    except Exception as e:
        return make_err_response(f'获取二维码失败: {str(e)}')
