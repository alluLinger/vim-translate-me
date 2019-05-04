# -*- coding: utf-8 -*-
# @Author: voldikss
# @Date: 2019-04-29 15:04:35
# @Last Modified by: voldikss
# @Last Modified time: 2019-04-29 15:04:35

import sys
import json
import random
import hashlib
import argparse
import codecs
import uuid
import time

if sys.version_info[0] == 2:
    from urllib2 import Request
    from urllib2 import urlopen
    from urllib import urlencode
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
else:
    from urllib.request import Request
    from urllib.request import urlopen
    from urllib.parse import urlencode
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)


class Query:
    def __init__(self, word, app_key, app_secret, to_lang):
        self.word = word
        self.app_key = app_key
        self.app_secret = app_secret
        self.to_lang = to_lang

    def baiduQuery(self):
        query_url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
        error_code = {
            '52000': '成功(Success)',
            '52001': '请求超时，请重试(HTTP request timed out, retry)',
            '52002': '系统错误，请重试(System error)',
            '52003': '未授权用户，请检查您的 appid 是否正确，或者服务是否开通(Unauthorized user, please check your appid or service)',
            '54000': '必填参数为空，请检查是否少传参数(Expected argument)',
            '54001': '签名错误，请检查您的签名生成方法(Sign error, please check your sign generation function)',
            '54003': '访问频率受限，请降低您的调用频率(Limited access frequency)',
            '54004': '账户余额不足，请前往管理控制台为账户充值(Insufficient balance for your account)',
            '54005': '长query请求频繁，请降低长query的发送频率，3s后再试(Too long and frequent requests)',
            '58000': '客户端IP非法(Invalid client IP address)',
            '58001': '译文语言方向不支持，检查译文语言是否在语言列表里(Not supported translation)',
            '58002': '服务当前已关闭，请前往管理控制台开启服务(Service has been closed, please start your service in the console)'
        }

        def buildQuery():
            data = {}
            salt = random.randint(32768, 65536)
            sign = self.app_key + self.word+str(salt) + self.app_secret
            m = hashlib.md5()
            m.update(sign.encode('utf-8'))
            sign = m.hexdigest()
            data['appid'] = self.app_key
            data['q'] = self.word
            data['from'] = 'auto'
            data['to'] = self.to_lang
            data['salt'] = salt
            data['sign'] = sign
            return urlencode(data)

        def vtmQuery():
            url = query_url + '?' + buildQuery()
            try:
                res = urlopen(url).read()
            except Exception as e:
                sys.stderr.write("网络请求错误(HTTP request error) %s" % e)
                return

            # sample of the response from the youdao server
            # SAMPLE_RESPONSE = {
            #     'from': 'en',
            #     'to': 'zh',
            #     'trans_result': [{'src': 'sample', 'dst': '样品'}]
            # }

            try:
                trans = {}
                data_json = json.loads(res.decode('utf-8'))
                if 'error_code' in data_json:
                    sys.stderr.write(error_code[data_json['error_code']])
                    return

                trans_result = data_json['trans_result'][0]
                trans['query'] = trans_result.get('src', 'null')
                trans['translation'] = trans_result.get('dst', 'null')

                sys.stdout.write(str(trans))
            except Exception as e:
                sys.stderr.write("数据解析错误(Data parsing error) Line[%s]：%s" % (
                    sys.exc_info()[2].tb_lineno, e))
                return

        vtmQuery()

    def bingQuery(self):
        query_url = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0'

        def vtmQuery():
            url = query_url + '&to=' + self.to_lang
            headers = {
                'Ocp-Apim-Subscription-Key': self.app_secret,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }

            body = [{
                'text': self.word
            }]

            try:
                if sys.version_info[0] == 2:
                    req = Request(url, headers=headers)
                    res = urlopen(req, json.dumps(body)).read()
                else:
                    req = Request(url, headers=headers)
                    json_d = json.dumps(body)
                    json_b = json_d.encode('utf-8')
                    req.add_header('Content-Length', len(json_b))
                    res = urlopen(req, json_b).read()
            except Exception as e:
                sys.stderr.write("网络请求错误(HTTP request error):%s" % e)
                return

            # sample response content:
            # sample_res = {'query': 'response', 'translation': '响应'}

            try:
                data_json = json.loads(res.decode('utf-8'))[0]
                if 'error' in data_json:
                    sys.stderr.write(data_json['error']['message'])
                    return

                trans = {}
                trans_result = data_json['translations'][0]
                trans['query'] = self.word
                trans['translation'] = trans_result.get('text', 'null')

                sys.stdout.write(str(trans))
            except Exception as e:
                sys.stderr.write("数据解析错误(Data parsing error)[%s]：%s" % (
                    sys.exc_info()[2].tb_lineno, e))
                return
        vtmQuery()

    def yandexQuery(self):
        query_url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
        error_code = {
            200: "Operation completed successfully",
            401: "Invalid API key",
            402: "Blocked API key",
            404: "Exceeded the daily limit on the amount of translated text",
            413: "Exceeded the maximum text size",
            422: "The text cannot be translated",
            501: "The specified translation direction is not supported"
        }

        def buildQuery():
            data = {}
            data['key'] = self.app_secret
            data['text'] = self.word.encode('utf-8')
            data['lang'] = self.to_lang
            return urlencode(data)

        def vtmQuery():
            url = query_url + '?' + buildQuery()

            try:
                res = urlopen(url).read()
            except Exception as e:
                sys.stderr.write("网络请求错误(HTTP request error):%s" % e)
                return

            # sample response content:
            # sample_res = {'code': 200, 'lang': 'en-zh', 'text': ['该应']}

            try:
                data_json = json.loads(res.decode('utf-8'))
                if data_json['code'] != 200:
                    sys.stderr.write(error_code[data_json['code']])
                    return

                trans = {}
                trans['query'] = self.word
                trans['translation'] = data_json.get('text', ['null'])[0]

                sys.stdout.write(str(trans))
            except Exception as e:
                sys.stderr.write("数据解析错误(Data parsing error) Line[%s]：%s" % (
                    sys.exc_info()[2].tb_lineno, e))
                return

        vtmQuery()

    def youdaoQuery(self):
        query_url = 'http://openapi.youdao.com/api'
        error_code = {
            '101': '缺少必填的参数(Expected arguments were not filled)',
            '102': '不支持的语言类型(Not supported language)',
            '103': '翻译文本过长(Text is too long to translate)',
            '104': '不支持的API类型(Not supported API)',
            '105': '不支持的签名类型(Not supported signature)',
            '106': '不支持的响应类型(Not supported response)',
            '107': '不支持的传输加密类型(Not supported transport encryption)',
            '108': 'appKey无效(Invalid appKey)',
            '109': 'batchLog格式不正确(Wrong format batchLog)',
            '110': '无相关服务的有效实例(No instance for relative service)',
            '111': '开发者账号无效(Invalid developer account)',
            '113': 'q不能为空(q can\' be empty)',
            '201': '解密失败(Failed to decode)',
            '202': '签名检验失败(Signature checking failed)',
            '203': '访问IP地址不在可访问IP列表(Not permitted IP address)',
            '205': '请求的接口与应用的平台类型不一致(The API you request isn\'t consistent with the platform of application)',
            '206': '因为时间戳无效导致签名校验失败(Signature checking failed due to invalid time stamp)',
            '207': '重放请求(Replay request)',
            '301': '辞典查询失败(Dictionary looking up failed)',
            '302': '翻译查询失败(Translation looking up failed)',
            '303': '服务端的其它异常(Other exception of server)',
            '401': '账户已经欠费停(Your account is out of credit)',
            '411': '访问频率受限,请稍后访问(Limited access frequency)',
            '412': '长请求过于频繁，请稍后访问(Long request is too frequent)'
        }

        def encrypt(sign_str):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(sign_str.encode('utf-8'))
            return hash_algorithm.hexdigest()

        def truncate(q):
            if q is None:
                return None
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

        def buildQuery():
            data = {}
            data['from'] = 'auto'
            data['to'] = self.to_lang
            data['signType'] = 'v3'
            curtime = str(int(time.time()))
            data['curtime'] = curtime
            salt = str(uuid.uuid1())
            sign_str = self.app_key + \
                truncate(self.word) + salt + curtime + self.app_secret
            sign = encrypt(sign_str)
            data['appKey'] = self.app_key
            data['q'] = self.word
            data['salt'] = salt
            data['sign'] = sign
            return urlencode(data)

        def vtmQuery():
            url = query_url + '?' + buildQuery()
            try:
                res = urlopen(url).read()
            except Exception as e:
                sys.stderr.write("网络请求错误(HTTP request error) %s" % e)
                return

            # sample of the response from the youdao server
            # SAMPLE_RESPONSE = {
            #     "tSpeakUrl": "...",
            #     "returnPhrase": ["test"],
            #     "web": [
            #         {"value": ["正交试验", "正交实验法", "正交设计"], "key":"orthogonal test"},
            #         {"value": ["双缩脲试剂", "二缩", "双脲试验"], "key":"biuret test"},
            #         {"value": ["项测试", "长期试验", "期中考试"], "key":"Term test"}],
            #     "query": "test",
            #     "translation": ["测试"],
            #     "errorCode": "0",
            #     "dict": {"url": "yddict://m.youdao.com/dict?le=eng&q=test"},
            #     "webdict": {"url": "http://m.youdao.com/dict?le=eng&q=test"},
            #     "basic": {
            #         "exam_type": ["高中", "初中"],
            #         "us-phonetic": "tɛst",
            #         "phonetic": "test",
            #         "uk-phonetic": "test",
            #         "uk-speech": "...",
            #         "explains": ["n. 试验；检验", "vt. 试验；测试", "vi. 试验；测试", "n. (Test)人名"],
            #         "us-speech": "..."
            #     },
            #     "l": "en2zh-CHS",
            #     "speakUrl": "..."
            # }

            try:
                data_json = json.loads(res.decode('utf-8'))
                if data_json['errorCode'] != "0":
                    sys.stderr.write(error_code[data_json['errorCode']])
                    return

                trans = {}
                trans['query'] = data_json['query']
                trans['translation'] = data_json['translation'][0]
                # sometimes data_json['basic'] is type <'None'>
                if 'basic' in data_json and data_json['basic']:
                    basic = data_json['basic']
                    if 'phonetic' in basic:
                        trans['phonetic'] = basic['phonetic']
                    if 'explains' in basic:
                        trans['explain'] = basic['explains']

                sys.stdout.write(str(trans))
            except Exception as e:
                sys.stderr.write("数据解析错误(Data parsing error) Line[%s]：%s" % (
                    sys.exc_info()[2].tb_lineno, e))
                return
        vtmQuery()


parser = argparse.ArgumentParser()

parser.add_argument('--word', required=False)
parser.add_argument('--api', required=False)
parser.add_argument('--appKey', required=False)
parser.add_argument('--appSecret', required=False)
parser.add_argument('--toLang', required=False)
parser.add_argument('--proxyHostname', required=False)
parser.add_argument('--proxyPort', required=False)
parser.add_argument('--proxyUsername', required=False)
parser.add_argument('--proxyPassword', required=False)

args = parser.parse_args()

if not args.word:    # for debug
    word = 'translation'
    to_lang = 'zh'
    app_key = '70d26c625f056dba'
    app_secret = 'trnsl.1.1.20190430T070040Z.b4d258419bc606c3.c91de1b8a30d1e62228a51de3bf0a036160b2293'
    query = Query(word, app_key, app_secret, to_lang)
    query.yandexQuery()
else:
    # todo
    # to trim the string's quote/doublequote(becase `shellescape` was used in autoload/vtm.vim)
    word = args.word.strip('\'')
    word = word.strip('\"')
    word = word.strip()
    api = args.api
    app_key = args.appKey
    app_secret = args.appSecret
    to_lang = args.toLang

    proxy_hostname = args.proxyHostname
    proxy_port = args.proxyPort
    proxy_username = args.proxyUsername
    proxy_password = args.proxyPassword

    if proxy_hostname != 'null' and proxy_port != 'null':
        import socks
        import socket
        ...

    query = Query(word, app_key, app_secret, to_lang)
    if api == 'baidu':
        query.baiduQuery()
    elif api == 'bing':
        query.bingQuery()
    elif api == 'yandex':
        query.yandexQuery()
    else:
        query.youdaoQuery()
