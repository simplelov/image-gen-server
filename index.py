#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# 确保images目录存在
os.makedirs('images', exist_ok=True)

# 导入Flask应用
from app import app

# 函数计算入口函数
def handler(environ, start_response):
    # 设置API密钥
    os.environ['JIMENG_API_TOKEN'] = '61e752e7c27c7b567f018a3160396a1e'
    return app.wsgi_app(environ, start_response)

# 本地测试用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
