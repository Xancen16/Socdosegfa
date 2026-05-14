from flask import request


def fix_ngrok_headers(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response