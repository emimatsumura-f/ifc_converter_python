document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#uploadForm');
    if (!form) return;

    const fileInput = document.getElementById('file-upload');
    const uploadBtn = form.querySelector('#uploadBtn');
    const spinner = uploadBtn ? uploadBtn.querySelector('.spinner-border') : null;
    const progressBar = document.getElementById('uploadProgress');
    const errorDiv = document.getElementById('errorMessage');
    const csrfToken = form.querySelector('input[name="csrf_token"]').value;

    let selectedFile = null;

    // ファイル選択時の処理
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.name.toLowerCase().endsWith('.ifc')) {
                    showError('IFCファイルのみアップロード可能です');
                    this.value = '';
                    selectedFile = null;
                    return;
                }
                selectedFile = file;
            }
        });
    }

    // アップロードボタンクリック時の処理
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!selectedFile) {
                showError('ファイルを選択してください');
                return;
            }
            uploadFile(selectedFile);
            if (uploadBtn) {
                uploadBtn.disabled = true;
                if (spinner) spinner.classList.remove('d-none');
            }
        });
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            uploadChunks(file, data.upload_id, data.chunk_size, data.chunks_total);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('アップロード準備中にエラーが発生しました');
        });
    }

    function uploadChunks(file, uploadId, chunkSize, totalChunks) {
        progressBar.style.display = 'block';
        progressBar.max = totalChunks;
        progressBar.value = 0;

        if (uploadBtn) {
            uploadBtn.disabled = true;
            if (spinner) spinner.classList.remove('d-none');
        }

        let uploadedChunks = 0;

        // チャンクごとのアップロード
        for (let chunkNumber = 0; chunkNumber < totalChunks; chunkNumber++) {
            const start = chunkNumber * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            const formData = new FormData();
            formData.append('chunk', chunk);

            fetch(`/upload/${uploadId}/chunk/${chunkNumber}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    resetUploadForm();
                    return;
                }

                uploadedChunks++;
                progressBar.value = uploadedChunks;

                if (data.status === 'completed') {
                    window.location.href = data.redirect;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError('チャンクのアップロード中にエラーが発生しました');
                resetUploadForm();
            });
        }
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    function resetUploadForm() {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            if (spinner) spinner.classList.add('d-none');
        }
        progressBar.style.display = 'none';
        progressBar.value = 0;
    }
});

// Featherアイコンの初期化
feather.replace();