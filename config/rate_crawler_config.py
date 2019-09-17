import os
import urllib

VST_URL = 'https://login.taobao.com/member/vst.htm?st={}'
MONGO_URI = os.environ.get('MONGODB', '192.168.3.21:32975')
PROXIES = {'http':'http:/122.117.138.228:80'}
LOGIN_URL = 'https://login.taobao.com/member/login.html'
LOGIN_HEADERS =  {
    'Host':'login.taobao.com',
    'User-Agent' : '5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'Referer' : 'https://login.taobao.com/member/login.html',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection' : 'Keep-Alive'
}
#用户名
username = 'TomLong530'
#ua字符串，taobao ua驗證碼
ua = '120#bX1bSaY8FInVXSZciIYfAMvfbcLJuQqj0QTchmQ4yNpC906/BeM0EpJt3tpqR/WB//hMnOvZ2fGGYK0ZM2GGP0BYmuMMEfPmqZiul2iDBYligFNgN6DB4HvwABZsTDi9wDIasPJXpmxemWgVjK0lmM4SfthPFud+n74qcccF16NI2pBzBIX+w+Hc8l9A5MDX9rTESNuuNeh6iGmhLDqfeo3gZ8bgVCj5hi4F3+hCbpLyknLFlAPslfktp6pISIYz515/yvVUTn5PNO8BbvbcTaMPyEIbS5hpNee/PbbSjMgaSTvVCJIO7vxYg6ikMx38XNnUMrYNqH5GGd3dSucNjOq0JN60oQ9PhVo56tsufgRfIcitTBANW1MXXMNuIuK+y2TcI4voAmrc2wuRjyjjaQk3tA4kzI27v+1dhVLUgshxwz60lzL0MjQA4eqzBTpSy0C++GdO+iBDg/nl02KUYZ9Ig+duucrop5HzeQzfnamUO0fcgrpKjZXN8tXvuZCQeF37s/J2wV5+uj6aHJp+YtyTYz/H6j9SZHyYCx9ZyG/uNgVgFB84/NmymOtRmrynkiUfLIM9ROy+46GYyTnFH0e1kCcLWvW/BliVVaLTX5W4WSUUnuQdtrhT/YvDCIUunPRHCZ2unRxrHfkyVuVm/OaZAVmkdl0+I4Kt42GwlRkqx2er2t6InahgfCRo446xvL0ZFzUIL5dG15XoIK+5uy+mmBusLxG9'
#密碼，透過taobao 加密
password2 = '5035134d53410c1a6f9567c737f0d346e79982880cded92d59c18bdd2284bc6b5b8ff9d7d874759806f6b34b0442003ef697cbdc4f4b6e8bbacfc17a0b75aeea9c1cbb5a2f78f03943c6d37a375115a6e441e621b7267b478d82401586003b043980a992998c528e97d36405adeea03ea8ed0ab75017ce0a593a554a68692b65'
post = {
    'TPL_username': username,
    'TPL_password_2': password2,
    'ua': ua,
    'TPL_redirect_url': 'http://i.taobao.com/my_taobao.htm?nekot=dG9tbG9uZzUzMA%3D%3D1567665966030',
    'TPL_password': '',
    'ncoSig': '',
    'ncoSessionid': '',
    'ncoToken': 'a3b8fcae9b63e74881eac8285fd8a5219f7909a4',
    'slideCodeShow': False,
    'useMobile': False,
    'lang': 'zh_CN',
    'loginsite': 0,
    'newlogin': 0,
    'TPL_redirect_url': '',
    'from': 'tb',
    'fc': 'default',
    'style': 'default',
    'css_style': '',
    'keyLogin': False,
    'qrLogin': True,
    'newMini': False,
    'newMini2': False,
    'tid': '',
    'loginType': 3,
    'minititle': '',
    'minipara': '',
    'pstrong': '',
    'sign': '',
    'need_sign': '',
    'isIgnore': '',
    'full_redirect': '',
    'sub_jump': '',
    'popid': '',
    'callback': '',
    'guf': '',
    'not_duplite_str': '',
    'need_user_id': '',
    'poy': '',
    'gvfdcname': 10,
    'gvfdcre': '',
    'from_encoding': '',
    'sub': '',
    'loginASR': 1,
    'loginASRSuc': 1,
    'allp': '',
    'oslanguage': 'zh-TW',
    'sr': '1440*900',
    'osVer': 'macos|10.136',
    'naviVer': 'chrome|75.03770142',
    'osACN': 'Mozilla',
    'osAV': '5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    'osPF': 'MacIntel',
    'miserHardInfo': '',
    'appkey': '00000000',
    'nickLoginLink': '',
    'mobileLoginLink': 'https://login.taobao.com/member/login.jhtml?useMobile=true',
    'showAssistantLink': True,
    'um_token': 'T7E1F6B7BDADF3AF0468FA984746D91447A94BE17BEC32A42B671C0253E',
}
#将POST的数据进行编码转换
POST_DATA = urllib.parse.urlencode(post).encode('gbk')