# -*- coding: utf-8 -*-
from flask import jsonify

def success_response(data=None, message="成功"):
    return jsonify({
        "code": 0,
        "message": message,
        "data": data
    })

def error_response(code, message="请求失败", data=None):
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), (code // 100) if code >= 10000 else 400
