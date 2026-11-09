# 検証記録

2026-11-09 / GitHub Actions / Debian 13 amd64 / QEMU + OVMF UEFI + TCG / 標準VGA

**`nova-os-0.1-amd64.iso` を生成し、Liveデスクトップへの起動を確認しました。**

## 取得先と検証の対応

- ISO生成：[実行42564094145](https://github.com/18s09000-afk/Nova-os/actions/runs/42564094145)
- Artifacts：`nova-os-0.1-amd64-2`、約2.3GB、ISOとSHA-256ファイルを収録
- 最新の成功した再検証：[実行42569015731](https://github.com/18s09000-afk/Nova-os/actions/runs/42569015731)
- [起動結果JSON](validation/boot-result.json) / [実際のGUI画面](screenshots/nova-os-0.1-live.png)

再検証では保存済みISOをダウンロードしてSHA-256を照合し、同じファイルを起動しました。
ISOを再生成・改変していません。検証コードのみ更新しています。
元のISO生成実行の赤いステータスは、修正前のテストによるものです。

| 検証内容 | 結果 |
|---|---|
| Debian 13公式パッケージの依存関係解決 | 成功（34指定パッケージと依存関係） |
| JSON・SVG・PNG構造 / シェル構文 / ShellCheck | 成功 |
| GRUB / Syslinuxの自動選択設定 | 実行テスト成功、UEFIで5秒後の自動起動も確認 |
| 英語・日本語のシリアルログインとQEMU早期終了の模擬検査 | 3ケース成功（OS起動とは別のプロトコル検査） |
| live-buildによるISO生成 | 2回成功 |
| 元のISOのSHA-256照合 | 成功 |
| UEFI → Linux → live-config → Liveログイン | 成功 |
| SDDM / KWin Wayland / Plasma / Fcitx5 | 動作確認 |
| PlasmaのD-Bus応答 / パネル数 | 成功 |
| Nova壁紙の選択値 | `org.kde.image` とNovaのPNGパスを確認 |
| 壁紙・ロゴ・下部パネル・ダーク配色・日本語表示 | QEMU画面を目視確認 |
| Mozcエンジン | 起動ログのロードとFcitx5プロセスを確認 |
| 日本語の実入力・変換操作 / 各アプリの操作 | 未検証 |
| 実機 / Secure Boot / 専用NVIDIAドライバー | 未検証 |
| Calamares / SSDへのインストール | 未実装・未実行 |

## 修正した問題

1. Codex Cloudのrootlessコンテナは、特権フラグ付きでも `mount` と `mknod` が拒否されました。
   実際のdebootstrapもマウント時に停止したため、GitHub提供ランナー上のrootful Dockerへ移しました。
2. Debian live-build標準GRUBにはタイムアウトがなく、初回はメニューで入力待ちでした。
   ISO作成前のbinary hookで5秒の自動選択を追加しました。
3. 日本語ログインの「パスワード:」をテストコードが認識できず、未認証の端末へ検査コマンドを送っていました。
   日本語・英語の認証状態を扱い、認証後にだけ検査するよう修正しました。
4. ヘッドレスQEMUは標準VGA構成で検証しました。ソフトウェア描画では初回フレームに時間がかかるため、
   デスクトップ応答確認後45秒待って画面を保存します。黒い初期フレームだけで描画不良と判定しません。

TLS・APT署名・チェックサム検証は無効化していません。
QEMUにはホストSSD・仮想ハードディスク・インストーラーを接続していません。

## 再検証・障害対処

- iPad：Actionsの **Retest existing Nova ISO** で元のビルド実行IDを指定。
- Linux：`python3 scripts/smoke-boot.py --iso <ISOのパス>`。
- 失敗時：`boot-result.json`、`qemu-serial.log`、`qemu-stderr.log`、PNG画面を確認。
- ログとPNGは `ci-diagnostics/` の専用ブランチにも保存。通常のソースは `main`。
- 容量・マウント制限で生成できない場合は、GitHub提供ランナーまたは十分な容量のLinuxクラウドVMを使用。
