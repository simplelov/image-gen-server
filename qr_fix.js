// 复制这段代码替换index.html中的分享二维码函数
// 搜索"// 分享二维码"然后替换下面的函数

// 分享二维码
window.showQR = function(src) {
    try {
        const url = window.location.origin + src;
        console.log('生成二维码URL:', url);
        
        // 先显示模态框
        const qrModal = document.getElementById('qrModal');
        const modal = new bootstrap.Modal(qrModal);
        modal.show();
        
        // 获取容器并清空
        const qrDiv = document.getElementById('qrcode');
        qrDiv.innerHTML = '';
        
        // 使用备用方法创建二维码
        try {
            // 创建新的QRCode实例
            new QRCode(qrDiv, {
                text: url,
                width: 180,
                height: 180,
                colorDark: "#000000",
                colorLight: "#ffffff"
            });
        } catch (error) {
            console.error('QRCode生成失败:', error);
            qrDiv.innerHTML = `
                <div class="alert alert-warning">
                    <strong>二维码生成失败</strong><br>
                    您可以手动复制链接：<br>
                    <input type="text" class="form-control mt-2 mb-2" value="${url}" readonly onclick="this.select()">
                    <button class="btn btn-sm btn-primary" onclick="navigator.clipboard.writeText('${url}'); alert('链接已复制')">复制链接</button>
                </div>
            `;
        }
    } catch (err) {
        console.error('分享功能出错:', err);
        alert('分享功能出错: ' + err.message);
    }
}
