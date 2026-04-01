# Supabase DB パスワードローテーション手順書

この手順書は、漏洩の可能性がある（または定期的なセキュリティ更新のための）データベースパスワードの変更手順を説明します。

## 1. Supabase ダッシュボードでの作業
1. Supabaseのプロジェクトダッシュボードにログインします。
2. 左側のメニューから **Settings (歯車アイコン)** をクリックします。
3. **Database** タブを選択します。
4. **Database password** セクションまでスクロールし、`Reset password` または `Change Password` をクリックします。
5. 強力な新しいパスワード（英数字・記号を組み合わせた16文字以上を推奨）を入力し、変更を保存します。
   - ※このパスワードは平文でローカルに保存しないようにしてください（`SUPABASE_CREDENTIALS.txt` などの使用は厳禁です）。

## 2. Render (バックエンドホスティング) 側の変数値更新
1. Renderのダッシュボードにログインし、Price-Radar の **Web Service**（バックエンド）を選択します。
2. **Environment** タブを開きます。
3. `DATABASE_URL` の環境変数を編集します。
   - **変更前**: `postgresql://postgres:旧パスワード@db.xxxx.supabase.co:5432/postgres`
   - **変更後**: `postgresql://postgres:新パスワード@db.xxxx.supabase.co:5432/postgres`
4. 変更を保存 (Save Changes) します。
5. Render が自動的に再デプロイを開始します（または手動で `Manual Deploy` をクリックします）。
6. Restart後、アプリケーションのログインやデータ取得が正常に行えるか確認してください。

## 3. その他の注意事項
* `alembic` のようなローカルでのマイグレーション作業や、`psql`コマンドでの直接接続を行う場合も、新しいパスワードを使用してください。
* 可能な限り、パスワードマネージャー (1Password, Bitwarden 等) でセキュアに管理してください。
