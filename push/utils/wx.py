# -*- coding: utf-8 -*-
import requests
from redis import Redis
import pickle
import time
import json
from .helper import request_api, get_redirect_url
from utils.func import random_ascii_string
import hashlib

APIROOT = 'https://api.weixin.qq.com'
URL = APIROOT + '/cgi-bin'


class WX:
    def __init__(self, app_id='', secret='', token=''):
        """
        连接微信，获取token
        """
        self.app_id = app_id
        self.secret = secret
        self.token = token

    def request_token(self):
        try:
            result = request_api(url='/token', params={
                'grant_type': 'client_credential',
                'appid': self.app_id,
                'secret': self.secret
            }, baseurl=URL)

            return result
        except Exception as e:
            return None
        
    def get_token(self, force=False):
        return self.token

    def request(self, url='', method='get', params=None, data=None, files=None, flag=False, baseurl=URL, headers=None, stream=False):
        """
        请求API接口，带access_token
        """
        if headers is None and not files:
            headers = {}
            headers['content-type'] = 'application/json; charset=utf-8'

        _params = params
        if not _params:
            _params = {}
        _params['access_token'] = self.get_token()

        _data = data
        if _data:
            _data = json.dumps(_data, ensure_ascii=False).encode('utf-8')

        r = getattr(requests, method)(baseurl + url, headers=headers, params=_params, data=_data, files=files, stream=stream)
        try:
            result = r.json()

            errcode = result.get('errcode')
            # token 过期重新请求，只会重试一次
            if errcode == 42001 or errcode == 40001:
                if flag is False:
                    self.get_token(force=True)
                    self.request(url=url, method=method, params=params, data=data, files=files, flag=True)
            else:
                if errcode > 0:
                    print '=' * 40
                    print result
                    print '=' * 40
                    return result
                    # raise ResponseMeta(description=result)
        except Exception, e:
            result = r
        return result

    def add_qrcode(self, chanel):
        """
        添加永久二维码，含渠道id
        """
        result = self.request(url='/qrcode/create', method='post', data={
            'action_name': 'QR_LIMIT_SCENE',
            'action_info': {
                'scene': {
                    'scene_str': chanel
                }
            }
        })
        return result

    @staticmethod
    def get_qrcode(ticket):
        """
        获取二维码图片的url
        """
        return 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=' + ticket

    def get_user_by_openid(self, openid):
        """
        获取用户信息
        """
        result = self.request(url='/user/info', params={
            'openid': openid,
            'lang': 'zh_CN'
        })
        return result

    def get_material_count(self):
        """
        获取素材库总数
        """
        result = self.request(url='/material/get_materialcount')
        return result

    def create_menu(self, menu):
        """
        创建菜单
        """
        result = self.request(url='/menu/create', method='post', data=menu)
        return result

    def delete_menu(self):
        """
        删除菜单
        """
        result = self.request(url='/menu/delete')
        return result

    def get_openid_by_code(self, code):
        """
        根据code获取用户的openid
        """
        result = request_api(url='/sns/oauth2/access_token', params={
            'appid': self.app_id,
            'secret': self.secret,
            'code': code,
            'grant_type': 'authorization_code'
        }, baseurl=APIROOT)
        return result

    def get_redirect_url(self, url):
        """
        利用oauth跳转，以便于菜单设置url后得到code从而进一步得到用户的openid
        """
        return get_redirect_url(self.app_id, url)

    def get_users(self, next_openid=''):
        """
        获取微信的关注用户
        """
        params = {}
        if next_openid:
            params['next_openid'] = next_openid
        result = self.request(url='/user/get', params=params)
        return result


    def send_text_message(self, openid, text):
        data = {
            'touser': openid,
            'msgtype': 'text',
            'text': {
                'content': text
            }
        }
        return self.send_message(data)

    def send_common_message(self, openid, msgtype, content):
        data = {
            'touser': openid,
            'msgtype': msgtype,
            msgtype: content
        }
        return self.send_message(data)

    def send_message(self, data):
        result = self.request('/message/custom/send', method='post', data=data)
        return result

    def send_template_message(self, openid, obj):
        url = obj.get('url')
        template_id = obj.get('template_id')
        data = {
            'touser': openid,
            'template_id': template_id,
            'data': obj.get('data')
        }
        if url:
            data['url'] = url

        result = self.request('/message/template/send', method='post', data=data)
        return result

    def add_media(self, media_type, media):
        result = self.request('/media/upload', method='post', params={
            'type': media_type
        }, files=media)
        return result

    def get_media(self, media_id):
        result = self.request(url='/media/get', headers={}, params={
            'media_id': media_id
        })
        return result

    def add_group(self, name):
        result = self.request(url='/groups/create', method='post', data={
            'group': {'name': name}
        })
        return result

    def get_groups(self):
        result = self.request(url='/groups/get')
        return result

    def set_group(self, group_id, openids):
        if isinstance(openids, list):
            result = self.request(url='/groups/members/batchupdate', method='post', data={
                'openid_list': openids,
                'to_groupid': group_id
            })
        else:
            result = self.request(url='/groups/members/update', method='post', data={
                'openid': openids,
                'to_groupid': group_id
            })
        return result

