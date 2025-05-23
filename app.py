from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import uuid
import requests
import re
from proxy.jimeng import generate_images, create_completion, create_completion_stream
from PIL import Image
import numpy as np

# 你可以在这里配置你的即梦 sessionid
JIMENG_API_TOKEN = "61e752e7c27c7b567f018a3160396a1e"

app = Flask(__name__, static_folder='static', template_folder='templates')

def safe_filename(prompt, ext='.jpg', folder=None):
    # 只保留中英文、数字、下划线、空格，替换其它为下划线
    name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_ ]', '_', prompt)
    name = name.strip().replace(' ', '_')
    if not name:
        name = uuid.uuid4().hex[:8]
    # 限制长度
    name = name[:40]
    filename = f"{name}{ext}"
    # 避免重名
    if folder:
        base, ext = os.path.splitext(filename)
        i = 1
        while os.path.exists(os.path.join(folder, filename)):
            filename = f"{base}_{i}{ext}"
            i += 1
    return filename

def parse_ratio(ratio, resolution):
    # ratio: "16:9" or "1:1" etc.
    try:
        w, h = map(int, ratio.split(':'))
        if w > 0 and h > 0:
            if w >= h:
                width = resolution
                height = int(resolution * h / w)
            else:
                height = resolution
                width = int(resolution * w / h)
            return width, height
    except Exception:
        pass
    return resolution, resolution

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 图片列表接口
@app.route('/api/images')
def list_images():
    images_dir = os.path.join(app.root_path, 'images')
    files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
    return jsonify({'images': files})

# 图片访问接口
@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(os.path.join(app.root_path, 'images'), filename)

# 删除图片接口
@app.route('/api/delete', methods=['POST'])
def delete_image():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'success': False, 'msg': '未指定文件名'})
    img_path = os.path.join(app.root_path, 'images', filename)
    if os.path.exists(img_path):
        os.remove(img_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'msg': '文件不存在'})

# 生成图片接口（直接调用 generate_images）
@app.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    style = data.get('style', 'default')
    ratio = data.get('ratio', '1:1')
    resolution = int(data.get('resolution', 1024))
    if not prompt:
        return jsonify({'success': False, 'msg': '描述不能为空', 'devMsg': 'Prompt is empty'})
    save_folder = os.path.join(app.root_path, 'images')
    file_name = safe_filename(prompt, '.jpg', save_folder)
    width, height = parse_ratio(ratio, resolution)
    sample_strength = 0.5
    try:
        # 1. 标准图片生成
        image_urls = generate_images(
            model="jimeng-2.1",
            prompt=prompt,
            width=width,
            height=height,
            sample_strength=sample_strength,
            negative_prompt="",
            refresh_token=JIMENG_API_TOKEN
        )
        if not image_urls:
            return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': 'No image url returned'})
        # 下载第一张图片
        img_url = image_urls[0]
        resp = requests.get(img_url)
        if resp.status_code == 200:
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            save_path = os.path.join(save_folder, file_name)
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            return jsonify({'success': True, 'filename': file_name})
        else:
            return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': f'Image download failed: {resp.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': str(e)})

# 预留：对话式生成接口
@app.route('/api/generate_chat', methods=['POST'])
def generate_image_chat():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'success': False, 'msg': '描述不能为空', 'devMsg': 'Prompt is empty'})
    try:
        result = create_completion([
            {"role": "user", "content": prompt}
        ], refresh_token=JIMENG_API_TOKEN)
        # 解析图片URL
        content = result['choices'][0]['message']['content']
        # 可用正则提取图片URL
        urls = re.findall(r'\((http[^)]+)\)', content)
        if not urls:
            return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': 'No image url returned'})
        img_url = urls[0]
        save_folder = os.path.join(app.root_path, 'images')
        file_name = safe_filename(prompt, '.jpg', save_folder)
        resp = requests.get(img_url)
        if resp.status_code == 200:
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)
            save_path = os.path.join(save_folder, file_name)
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            return jsonify({'success': True, 'filename': file_name})
        else:
            return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': f'Image download failed: {resp.status_code}'})
    except Exception as e:
        return jsonify({'success': False, 'msg': '网络开小差了呢，请重新尝试~', 'devMsg': str(e)})

# 预留：流式生成接口（可用于前端轮询/进度）
# @app.route('/api/generate_stream', methods=['POST'])
# def generate_image_stream():
#     # 可参考 create_completion_stream 的用法
#     pass

def get_image_path(filename):
    return os.path.join(app.root_path, 'images', filename)

@app.route('/api/facefix', methods=['POST'])
def facefix_image():
    data = request.get_json()
    filename = data.get('filename')
    if not filename or not os.path.exists(get_image_path(filename)):
        return jsonify({'success': False, 'msg': '未找到图片', 'devMsg': 'File not found'})
    try:
        from gfpgan import GFPGANer
        img = Image.open(get_image_path(filename)).convert('RGB')
        model = GFPGANer(model_path='weights/GFPGANv1.4.pth', upscale=1, arch='clean', channel_multiplier=2, bg_upsampler=None)
        _, _, output = model.enhance(np.array(img), has_aligned=False, only_center_face=False, paste_back=True)
        output_img = Image.fromarray(output)
        new_name = filename.rsplit('.',1)[0] + '_facefix.jpg'
        output_img.save(get_image_path(new_name))
        return jsonify({'success': True, 'filename': new_name})
    except Exception as e:
        return jsonify({'success': False, 'msg': '人脸修复失败，请稍后重试~', 'devMsg': str(e)})

# 确保images文件夹存在
os.makedirs('images', exist_ok=True)

# 在生产环境中禁用调试模式
if __name__ == '__main__':
    # 从环境变量获取端口，这对云平台部署很重要
    port = int(os.environ.get('PORT', 5000))
    # 在生产环境中使用0.0.0.0以接受所有传入连接
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')