# UNFINISHED!!!!!!!!! TRANSLATOR NEEDED TO TRANSLATE THE ENG README to JPN

# genon2nnsvs
 UTAU音源の原音をNNSVSで学習できるようにする。

## 開発環境

- Windows10
- Python3.8
- utaupy 開発版
- WSL1 (Ubuntu 20.04)

## 使い方

### UTAU音源の前処理

1. UTAU音源の各音階を moresampler で原音設定しなおす。（設定：日本語VCV、連番なし、エイリアスへのprefix追加なし）
2. [oto_estimation_checker](https://github.com/oatsu-gh/oto_estimation_checker) で原音設定ミスを検出する。手動チェックでもよい。
3. setParam を使って原音設定ミスを直す。オーバーラップが子音開始位置、先行発声が母音開始位置となるようにする。
4. 原音設定ファイルの右ブランクを正にする。setParamで一括変換するか、[force_otoini_cutoff_negative](https://github.com/oatsu-gh/oto2lab/tree/master/tool/force_otoini_cutoff_negative) を使う。

### 歌唱データベース化

1. **01_genon2db.py** を実行して、dataフォルダ内にlabファイルを生成し、wavファイルをコピーする。ついでにustも生成される。
2. 多音階音源の場合、各収録音階に対して1の作業を実施する。

### 学習準備

1. **02_place_files.py** を実行して、 acoustic、duration、timelag モデルの学習用フォルダに各種学習ファイルを配置する。
2. **03_generate_train_list.py** を実行して、曲名リストのファイルを作る。（dev, eval, utt_list とか）

### 学習

1. **config.yaml** を必要に応じて書き換える。
2. **run.sh** のステージ1以降を実行する。
