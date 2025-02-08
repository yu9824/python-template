## リモートリポジトリの削除

ローカルに同じ名前のリモートリポジトリを一括削除するコマンド。

```bash
git branch -r | grep -v 'main\|gh-page' | sed 's/origin\///' | xargs -I {} git push origin --delete {}
```

`main` と `gh-page` 以外のリモートリポジトリが削除される。（対応するローカルのブランチも削除されるのかは不明。）

## ローカルリポジトリの削除

```bash
git branch | grep -v "main" | xargs git branch -d
```

`main` 以外のリポジトリが削除できる。

この場合マージしてないブランチは保護される。削除するには `-d` を `-D` にする。
