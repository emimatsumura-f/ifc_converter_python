// フォームの送信イベントを監視
document.getElementById('signupForm').addEventListener('submit', function(e) {
    // フォームのデフォルトの送信動作を防止
    e.preventDefault();

    // フォームの各入力値を取得
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    // 入力値の空チェック
    if (!username || !email || !password) {
        // エラーメッセージを表示
        errorMessage.style.display = 'block';
        errorMessage.textContent = '全ての項目を入力してください。';
        return;
    }

    // メールアドレスの形式チェック（@が含まれているか）
    if (!email.includes('@')) {
        // エラーメッセージを表示
        errorMessage.style.display = 'block';
        errorMessage.textContent = '有効なメールアドレスを入力してください。';
        return;
    }

    // パスワードの長さチェック（6文字以上）
    if (password.length < 6) {
        // エラーメッセージを表示
        errorMessage.style.display = 'block';
        errorMessage.textContent = 'パスワードは6文字以上で入力してください。';
        return;
    }

    // デバッグ用：登録情報をコンソールに出力
    console.log('登録されたユーザー情報:', {
        username: username,
        email: email,
        password: password
    });

    // 登録成功時にログイン画面へリダイレクト
    window.location.href = 'index.html';
});