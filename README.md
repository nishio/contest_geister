# contest_geister
コンテスト参加用ガイスター思考ルーチン



# LOG

やったことをメモしておかないと、次にこれを見た時に思い出せないのでなんでもメモしておく。

## 2017-11-05

コンテストに本人不参加でプログラムだけ参加することになったので、
代理人が容易に起動できるようにする必要がある。
過去の色々な実験が複数のリポジトリに分かれているのでこの機会にまとめる。

### client.py

gpcc_geisterからコピー、三好さんのサーバーに接続して対戦できることが確認済みのもの。

引数なしで起動して人間との対戦ができることを確認。

### pomcp.py

reinforcement_learningからコピー。サーバとの接続をしないPOMCPの実装。

これをclient.pyから呼び出せるようにする。

### geister.py

gpcc_geisterからex1をコピーしgetster.pyにリネーム。
pomcpの中でインポートして使っていたので。理由などは完全に忘れた。

### AI

client.pyのなかのクラスAIが、思考ルーチン用の共通インターフェイスに見える。
これを継承してchoose_red_ghostsとchoose_next_moveを実装すれば良さそう。
無引数で起動したときに起動されるAIはこの行で決まっている `DefaultAI = FastestColorblindAI` 

とりあえずPartiallyObservableAIってのを作る。

### ghosts

choose_next_moveが引数として受け取るghostsってなんだ？
connect_serverの中で、message_to_ghostsでサーバからのレスポンスをパースしてた。

```
from collections import namedtuple
Ghost = namedtuple("Ghost", "name pos color")

TEST_GHOSTS = [Ghost('A', (1, 4), 'R'), Ghost('B', (2, 4), 'R'), Ghost('C', (3, 4), 'R'), Ghost('D', (4, 4), 'R'), Ghost('E', (1, 5), \
'B'), Ghost('F', (2, 5), 'B'), Ghost('G', (3, 5), 'B'), Ghost('H', (4, 5), 'B'), Ghost('a', (4, 1), 'u'), Ghost('b', (3, 1), 'u'), Gho\
st('c', (2, 1), 'u'), Ghost('d', (1, 1), 'u'), Ghost('e', (4, 0), 'u'), Ghost('f', (3, 0), 'u'), Ghost('g', (2, 0), 'u'), Ghost('h', (\
1, 0), 'u')]
```

### view

一方でPOMCP#choiceが受け取るのはviewってオブジェクト。これは「見えてはいけない情報が見えないように」という意図のものなので
意味合い的にはサーバが送ってくる情報と同じハズ

client.py側で差異を吸収する手とpomcp.py側でghostsを扱えるように修正するかの二通りがあるが、
どっちみち対戦時間制限などでpomcp.py側を今回のコンテストにあわせて書き換えるのだから、後者でやろう。

### 補欠選手

pomcp.pyはPartiallyObservableAIが選ばれた時だけロードされるようにしたので、
中がどうなっていようが他のAIを使う分には影響はない。
pomcp.pyの中をギリギリまで書き換えて、もし間に合わなければ「--ai=Sub」とオプションに付けて補欠選手で起動してもらおう。

