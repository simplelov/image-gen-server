// 分享二维码 - 修复版本
function showQR(src) {
    try {
        const url = window.location.origin + src;
        console.log('正在生成二维码，URL:', url);
        const qrDiv = document.getElementById('qrcode');
        qrDiv.innerHTML = '';
        
        // 创建一个canvas元素
        const canvas = document.createElement('canvas');
        qrDiv.appendChild(canvas);
        
        // 使用QRCode库生成二维码
        QRCode.toCanvas(canvas, url, {width:180, margin:1}, function (error) {
            if (error) {
                console.error('二维码生成失败:', error);
                qrDiv.innerHTML = '<div class="alert alert-danger">二维码生成失败</div>';
            } else {
                console.log('二维码生成成功');
            }
        });
        
        // 正确初始化和显示Bootstrap 5模态框
        const qrModal = document.getElementById('qrModal');
        const modal = new bootstrap.Modal(qrModal);
        modal.show();
    } catch (err) {
        console.error('分享功能出错:', err);
        alert('分享功能出错: ' + err.message);
    }
}
