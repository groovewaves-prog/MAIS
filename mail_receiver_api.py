from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
from get_filter_info import application as get_filter_info
from post_mail_info import application as post_mail_info

def router(env, start_response):
    path = env['PATH_INFO']
    if path == '/mail_receiver_api/get_filter_info':
        return get_filter_info(env, start_response)
    elif path == '/mail_receiver_api/post_mail_info':
        return post_mail_info(env, start_response)
    else:
        start_response('404 NOT FOUND', [])
        return [b""]

if __name__ == '__main__':
    #コマンドライン起動することによってテストサーバーを実行する
    with make_server('', 8888, router) as httpd:
        print("Serving on port 8888...")
        httpd.serve_forever()
