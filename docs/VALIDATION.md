# 検証記録

2026-11-09 / Codex Cloud / Debian 13 amd64

| 項目 | 結果 |
|---|---|
| オリジナル設定・アートワークの作成 | 完了 |
| JSON・SVG・PNG構造、34パッケージ名の検査 | 成功 |
| ShellCheck / シェル構文 | 成功 |
| live-build 1:20250505+deb13u1 による設定生成 | 成功 |
| 公式trixie + trixie-securityの依存関係解決 | 成功（インストールシミュレーション） |
| Plasma 6.3.6 Waylandセッションのファイル名 | Debianパッケージ内容を確認 |
| Fcitx5仮想キーボード用desktopエントリー | Debianパッケージ内容を確認 |
| live-build実行 | ベース取得・検証後、debootstrapのマウントで停止 |
| QEMU 10.0.13 / TCG / OVMF UEFI | ファームウェアのみ起動・QMP応答・画面取得成功 |
| Nova ISO生成 | 未完了 |
| NovaのUEFI起動・Plasma画面・日本語入力 | 未検証 |
| GitHub Actionsでの実行 | まだ実行結果を取得していない |

## クラウドで確認した制約

特権フラグ付きrootless Dockerでも `mount -t tmpfs` と `mknod` が拒否されました。
実際のlive-buildはDebianパッケージの取得・検証後に次で停止しました：

```text
mount: .../chroot/test-dev-null: permission denied.
E: Cannot install into target '.../chroot' mounted with noexec
```

これは権限の制限によるものです。TLS・APT署名・チェックサム検証の無効化や
debootstrapの安全チェック削除は行っていません。
GitHub提供ランナー上のrootful Dockerを代替にしました。そこでのビルド・起動結果は
ActionsとArtifactsの `boot-result.json` で確認してください。

## 障害対処

- `mount permission denied`: rootful Dockerの特権コンテナまたは完全なDebian VMで実行。
- パッケージが見つからない: `dist/package-resolution.log`、ミラー接続、archive areasを確認。
- 容量不足: 容量の大きいクラウドランナーで再実行。実機SSDの操作は不要。
- 起動タイムアウト: `qemu-stderr.log`、`qemu-serial.log`、画面を確認。
  ISOが作成されていても、その状態では起動確認済みとは扱わない。
- PlasmaやFcitx5が起動しない: シリアルログイン後に `journalctl -b`、
  `systemctl status sddm`、`loginctl` で原因を確認。検査条件を弱めて通さない。
