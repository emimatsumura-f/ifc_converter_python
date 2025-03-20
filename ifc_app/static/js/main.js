document.addEventListener('DOMContentLoaded', function() {
    // ファイルアップロードフォームの処理
    const uploadForms = document.querySelectorAll('#uploadForm');

    uploadForms.forEach(form => {
        const fileInput = form.querySelector('input[type="file"]');
        const uploadBtn = form.querySelector('#uploadBtn');
        const spinner = uploadBtn ? uploadBtn.querySelector('.spinner-border') : null;
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress mb-3 d-none';
        progressContainer.innerHTML = `
            <div class="progress-bar" role="progressbar" style="width: 0%"
                 aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
        `;

        if (fileInput) {
            // プログレスバーをファイル入力の後に挿入
            fileInput.parentNode.insertBefore(progressContainer, fileInput.nextSibling);

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

        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();

                const formData = new FormData(this);
                const xhr = new XMLHttpRequest();

                // プログレスバーの表示
                progressContainer.classList.remove('d-none');
                if (uploadBtn) {
                    uploadBtn.disabled = true;
                    if (spinner) {
                        spinner.classList.remove('d-none');
                    }
                    uploadBtn.textContent = ' アップロード中...';
                    if (spinner) {
                        spinner.parentNode.insertBefore(spinner, uploadBtn.firstChild);
                    }
                }

                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        const progressBar = progressContainer.querySelector('.progress-bar');
                        progressBar.style.width = percentComplete + '%';
                        progressBar.setAttribute('aria-valuenow', percentComplete);
                        progressBar.textContent = Math.round(percentComplete) + '%';
                    }
                });

                xhr.addEventListener('load', function() {
                    if (xhr.status === 200 || xhr.status === 302) {
                        window.location.href = xhr.responseURL || xhr.response;
                    } else {
                        alert('アップロード中にエラーが発生しました');
                        if (uploadBtn) {
                            uploadBtn.disabled = false;
                            if (spinner) {
                                spinner.classList.add('d-none');
                            }
                            uploadBtn.textContent = 'アップロードして解析';
                        }
                        progressContainer.classList.add('d-none');
                    }
                });

                xhr.addEventListener('error', function() {
                    alert('アップロード中にエラーが発生しました');
                    if (uploadBtn) {
                        uploadBtn.disabled = false;
                        if (spinner) {
                            spinner.classList.add('d-none');
                        }
                        uploadBtn.textContent = 'アップロードして解析';
                    }
                    progressContainer.classList.add('d-none');
                });

                xhr.open('POST', form.action, true);
                xhr.send(formData);
            });
        }
    });

    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const spinner = uploadBtn.querySelector('.spinner-border');

    if (uploadForm) {
        uploadForm.addEventListener('submit', function() {
            // アップロードボタンを無効化
            uploadBtn.disabled = true;
            // スピナーを表示
            spinner.classList.remove('d-none');
            // ボタンのテキストを変更
            uploadBtn.textContent = 'アップロード中...';
        });
    }
});

// Featherアイコンの初期化 (from original code)
feather.replace();