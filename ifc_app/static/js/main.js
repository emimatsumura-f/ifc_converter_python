document.addEventListener('DOMContentLoaded', function() {
    // CSRFトークンの取得
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    const form = document.querySelector('#uploadForm');
    if (!form) return;

    const fileInput = document.getElementById('file-upload');
    const uploadBtn = form.querySelector('#uploadBtn');
    const spinner = uploadBtn ? uploadBtn.querySelector('.spinner-border') : null;
    const progressBar = document.getElementById('uploadProgress');
    const errorDiv = document.getElementById('errorMessage');

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
            showError('アップロード中にエラーが発生しました');
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
                showError('アップロード中にエラーが発生しました');
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

    // 履歴機能の実装
    const historyTable = document.querySelector('.history-table');
    if (historyTable) {
        // 履歴テーブルのイベント処理
        historyTable.addEventListener('click', function(e) {
            // 削除ボタンのクリック処理
            const deleteButton = e.target.closest('.delete-history');
            if (deleteButton) {
                e.preventDefault();
                e.stopPropagation();
                const historyId = deleteButton.dataset.historyId;
                if (confirm('この履歴を削除してもよろしいですか？')) {
                    deleteHistory(historyId);
                }
            }

            // ファイル名のクリック処理
            const filenameLink = e.target.closest('.history-filename');
            if (filenameLink) {
                e.preventDefault();
                e.stopPropagation();
                const historyId = filenameLink.dataset.historyId;
                showPreview(historyId);
            }
        });
    }

    function deleteHistory(historyId) {
        fetch(`/history/${historyId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const row = document.querySelector(`tr[data-history-id="${historyId}"]`);
                if (row) {
                    row.remove();
                    // テーブルが空になった場合、メッセージを表示
                    if (document.querySelectorAll('.history-table tbody tr').length === 0) {
                        const cardBody = document.querySelector('.card-body');
                        cardBody.innerHTML = '<div class="alert alert-info">まだ変換履歴がありません。</div>';
                    }
                }
            } else {
                alert(data.error || '削除中にエラーが発生しました');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('削除中にエラーが発生しました');
        });
    }

    function showPreview(historyId) {
        window.location.href = `/preview/${historyId}`;
    }
});

// Featherアイコンの初期化
feather.replace();