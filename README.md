# contest_geister
コンテスト参加用ガイスター思考ルーチン

Python2系＋Numpyが必要。

## 使い方

client.pyを引数なしで起動すると三好さんのサーバに接続してGUIを出し人間対戦モードに入る

client.py --help でオプションの一覧が出る。--serverでサーバのIPアドレスを指定し、--portで接続するポートを指定すれば使えるはず。

## LOG

やったことをメモしておかないと、次にこれを見た時に思い出せないのでなんでもメモしておく。

#### 2017-11-05

コンテストに本人不参加でプログラムだけ参加することになったので、
代理人が容易に起動できるようにする必要がある。
過去の色々な実験が複数のリポジトリに分かれているのでこの機会にまとめる。

コンテスト: http://www2.matsue-ct.ac.jp/home/hashimoto/geister/

#### client.py

gpcc_geisterからコピー、三好さんのサーバーに接続して対戦できることが確認済みのもの。

引数なしで起動して人間との対戦ができることを確認。

#### pomcp.py

reinforcement_learningからコピー。サーバとの接続をしないPOMCPの実装。

これをclient.pyから呼び出せるようにする。

#### geister.py

gpcc_geisterからex1をコピーしgetster.pyにリネーム。
pomcpの中でインポートして使っていたので。理由などは完全に忘れた。

#### AI

client.pyのなかのクラスAIが、思考ルーチン用の共通インターフェイスに見える。
これを継承してchoose_red_ghostsとchoose_next_moveを実装すれば良さそう。
無引数で起動したときに起動されるAIはこの行で決まっている `DefaultAI = FastestColorblindAI` 

とりあえずPartiallyObservableAIってのを作る。

#### ghosts

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

#### view

一方でPOMCP#choiceが受け取るのはviewってオブジェクト。これは「見えてはいけない情報が見えないように」という意図のものなので
意味合い的にはサーバが送ってくる情報と同じハズ

client.py側で差異を吸収する手とpomcp.py側でghostsを扱えるように修正するかの二通りがあるが、
どっちみち対戦時間制限などでpomcp.py側を今回のコンテストにあわせて書き換えるのだから、後者でやろう。

#### 補欠選手

pomcp.pyはPartiallyObservableAIが選ばれた時だけロードされるようにしたので、
中がどうなっていようが他のAIを使う分には影響はない。
pomcp.pyの中をギリギリまで書き換えて、もし間に合わなければ「--ai=Sub」とオプションに付けて補欠選手で起動してもらおう。

#### View

Viewはv.dead_blueみたいな形で読みやすい形で情報を取り出せるように設計されている。
ghostsはパースされただけのただのリストなので、それをpomcp.pyの中でViewに変換してやればいいように思う。

Viewはgeister.Gameのto_viewの返り値としても返ってくるので、まるっとgeister.pyまで書き換えるよりは、
pomcp.pyがアダプタとして差異を吸収してしまうのが良さそう。

#### Viewその2

ダメだ。Viewの作成時に、相手のコマを「生きているもの」「死んだ青の個数」「死んだ赤の個数」という値に変換しているが、これでは「いま生きてる1番目のコマが、元々どこのコマだったか」がわからない。サーバからのメッセージは、何番目のコマが死んだかの情報を保っているので、不必要な抽象化によって情報が捨てられている。

サーバ https://github.com/miyo/geister_server.java/

geister.pyの中身を読んだけども、小さいサイズの盤でコードを共通化して実験をしてて無駄に複雑。

#### View、実験

ViewとGameを書き換えるべきか、アダプタで何とかなるか実験するために、テスト用のコードを作成。

sample_from_initial_observationの中で、与えられたghostsからGameの形にするコードが複雑。
とりあえずモックで初期状態ゲームを返すようにし、
make_new_historyの中でリストの場合は文字列に変換するようにした(hashableにするため)ら、
2手プレイすることができた。

#### バグ

こんな間違いが…

```
def calc_new_pos(pos, direction):
    if direction == 'N':
        return (pos[0], pos[1] - 1)
    if direction == 'E':
        return (pos[0] + 1, pos[1])
    if direction == 'W':
        return (pos[0], pos[1] + 1)
    if direction == 'S':
        return (pos[0] - 1, pos[1])
    raise AssertionError('not here')
```

#### 対応付け

バグの原因が東西南北が逆になっていることかと勘違いしたが、そうではない。

geister.pyが「青4つ赤4つ」の「位置*8」のリストで管理していてclient.pyが「初期配置順」の「(色, 位置) * 8」のリストで管理しているため、geister.py側の返してきた「コマID」をそのままゲームサーバに返すとエラーになるというもの。

そこを直してだいぶプレイできるようになったが、それでもたまに死んでるコマを動かそうとしてエラーになる。これも対応付け周りのバグかなぁ。

0から作り直すならgeister.py側をゲームサーバやclient.pyにあわせ実装に置き換えたい。

#### 死にコマの扱い

ゲームサーバは死んだコマの位置を(9, 9)で送ってくるが、geister.pyは位置を整数で扱っていて、36を死にコマとして扱っていた。このミスマッチで、死んだコマが死んだとみなされていなかった。

#### 自分の死にコマの色

自分の赤コマは常にRだと思い込んでいたが、死ぬとrになる。これはサーバ仕様にちゃんと明記されている。死ぬと両者に色が公開されるためrになる。

>色(相手に非公開の赤/青=R/B，両者が見えている赤=r/青=b/不明=u)

#### ぐぬぬ、いい勝負だぞ

https://gyazo.com/67c21750b7ffd54c8e631731e56a0f4c

この後、包囲網をすり抜けたコマがゴールに走り込み、1手差で間に合わず負けたかと思ったが、ゴールインの手にバグがありプログラムが異常終了したので人間の勝ち。

#### ゴールイン時のバグ

ゴールインアクションを行ったときのpomcpのactionはこう: `['2' 'WIN']`

コマIDが文字列になっているせいで対応付けに失敗している。これはgeister.pyがアクションを上下左右の移動量(整数)で表現しているのに、ゴールインのアクションだけ'WIN'という文字列になっていることが1つ目の原因。それ単独では問題は起きなかったがpomcp.pyではNumpyを使っている。Numpyでは文字列の混ざっているリストをarrayにすると、整数まで文字列に変換される。

```
>>> numpy.array([1, "a"])
array(['1', 'a'],
      dtype='|S21')
```

geister.pyを作り直す際には、アクションに整数を振ってやる必要がある。

サーバは特に「ゴールインする」というアクションを用意していない。
角まで進んでから矢印の方向に進めばゴールとみなされる。
なのでgeister.pyから"WIN"が返ってきたタイミングで、適切な方向への移動に置き換えてやればよい。
#### 何とか動いた

上記の修正を行って、何とかバラバラだったプロジェクトを一つに合体させて動作させることができた。どれくらいかかるかの見積もりができていなかったので、ひやひやした。最悪間に合わなかったらクライアントのテスト用のしょぼいものを出す羽目になるところだった。

とりあえず client.py --random-test --endless で変なバグが残っていないかずっとテストを掛けておこう。

今のバージョンには、中の実装を把握している僕にとってはハメ技が存在して勝とうと思えばいつでも勝てる。実装を把握していない人がプレイしたときにどうなるか興味深い(夏のプロシンでアルゴリズムの解説をしたときは、内情を知らない人とは意外と良い勝負をするのではないかと指摘された)

#### 今回のコンテスト用の修正

1手10秒なので9秒間探索するようにする。(今までは1秒だった)

#### HTTP版のアイデア

HTTPで盤面を受け取って手を返すHTTPサーバをWeb上に公開して、そこにリクエストを投げて結果を返すだけのクライアントを用意しておけばリモートでコンテストに参加する時に環境構築を気にしなくてよい。

#### 色を推測しないAIに関する考察


