document.addEventListener('DOMContentLoaded', function() {
    // フォーム要素の取得（IDセレクタを使用）
    const form = document.querySelector('#uploadForm');
    if (!form) return;

    const fileInput = form.querySelector('input[type="file"]');
    const uploadBtn = form.querySelector('#uploadBtn');
    const spinner = uploadBtn ? uploadBtn.querySelector('.spinner-border') : null;
    
    // プログレスバーコンテナの作成
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress mb-3 d-none';
    progressContainer.innerHTML = `
        <div class="progress-bar" role="progressbar" style="width: 0%"
             aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
    `;

    // プログレスバーの挿入位置を特定
    if (fileInput && fileInput.parentElement) {
        fileInput.parentElement.insertBefore(progressContainer, fileInput.nextSibling);
    }

    // ファイル選択時の処理
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                if (!file.name.toLowerCase().endsWith('.ifc')) {
                    alert('IFCファイルを選択してください');
                    this.value = '';
                } else if (file.size > 100 * 1024 * 1024) { // 100MB
                    alert('ファイルサイズは100MB以下にしてください');
                    this.value = '';
                }
            }
        });
    }

    // フォームサブミット時の処理
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // ファイルチェック
        const formData = new FormData(this);
        if (!formData.get('file')) {
            alert('ファイルを選択してください');
            return;
        }

        const xhr = new XMLHttpRequest();

        // プログレスバーの表示
        progressContainer.classList.remove('d-none');
        
        // ボタンの状態を更新
        if (uploadBtn) {
            uploadBtn.disabled = true;
            if (spinner) {
                spinner.classList.remove('d-none');
            }
            uploadBtn.textContent = ' アップロード中...';
            if (spinner) {
                uploadBtn.insertBefore(spinner, uploadBtn.firstChild);
            }
        }

        // アップロードの進捗処理
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                const progressBar = progressContainer.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = percentComplete + '%';
                    progressBar.setAttribute('aria-valuenow', percentComplete);
                    progressBar.textContent = Math.round(percentComplete) + '%';
                }
            }
        });

        // レスポンス処理
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    } else if (response.error) {
                        alert(response.error);
                        resetUploadForm();
                    }
                } catch (e) {
                    console.error('Response parsing error:', e);
                    alert('レスポンスの処理中にエラーが発生しました');
                    resetUploadForm();
                }
            } else {
                try {
                    const response = JSON.parse(xhr.responseText);
                    alert(response.error || 'アップロード中にエラーが発生しました');
                } catch (e) {
                    // HTMLレスポンスの場合（認証エラーなど）
                    if (xhr.responseText.includes('<!DOCTYPE')) {
                        window.location.reload(); // セッション切れの場合はページをリロード
                    } else {
                        alert('アップロード中にエラーが発生しました');
                    }
                }
                resetUploadForm();
            }
        });

        xhr.addEventListener('error', function() {
            alert('アップロード中にエラーが発生しました');
            resetUploadForm();
        });

        function resetUploadForm() {
            if (uploadBtn) {
                uploadBtn.disabled = false;
                if (spinner) {
                    spinner.classList.add('d-none');
                }
                uploadBtn.textContent = 'アップロードして解析';
            }
            progressContainer.classList.add('d-none');
        }

        // CSRFトークンの取得と設定
        const csrfToken = form.querySelector('input[name="csrf_token"]').value;
        
        // リクエストの送信
        const url = form.getAttribute('action');
        if (!url) {
            alert('アップロードURLが設定されていません');
            return;
        }

        xhr.open('POST', url, true);
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
        xhr.send(formData);
    });
});

// Featherアイコンの初期化
feather.replace();