#!/usr/bin/env python3
# Copyright (c) 2020 oatsu
"""
収録音声に対応するUSTファイルを生成する。

1. oto.iniファイルからBPMを推定する。
2. 使う音階を指定する。
3. 通常連続音か、歌連続音か選択する。
4. USTオブジェクトを生成する。
"""
from glob import glob
from operator import attrgetter
from os import makedirs
from os.path import abspath, basename, dirname, isdir, join
from shutil import copy
from typing import List, Tuple, Dict, Optional
import pathlib

import utaupy as up
import yaml
from pydub import AudioSegment
from tqdm import tqdm
from utaupy.otoini import OtoIni
from utaupy.ust import NOTENAME_TO_NOTENUM_DICT


def force_otoinifile_cutoff_negative(path_otoini_in, path_otoini_out, encoding='cp932'):
    """
    指定されたoto.iniを読んで、右ブランクが正の値なときはwavファイルの長さを調べて負にする。
    """
    otoini = up.otoini.load(path_otoini_in, encoding = encoding)
    voice_dir = dirname(path_otoini_in)
    if any([oto.cutoff > 0 for oto in otoini]):
        for oto in otoini:
            path_wav = join(voice_dir, oto.filename)
            sound = AudioSegment.from_file(path_wav, 'wav')
            duration_ms = 1000 * sound.duration_seconds
            absolute_cutoff_position = duration_ms - oto.cutoff
            oto.cutoff = -(absolute_cutoff_position - oto.offset)
        otoini.write(path_otoini_out, encoding = encoding)


def prepare_otoini(otoini: OtoIni):
    """
    OtoIniオブジェクトをUSTにしやすいように前処理する。

    - OtoIni中のエイリアスを絞り込む。
        - 「息」と「を」を除去する
    - 語尾音素を「a -」→「a R」に変換する。
    - 連続音エイリアスを単独音化する。
    - ソートする。

    破壊的処理
    """
    # ブレスと「を」を除去する。ないと思うが単独音エイリアスも除去する。
    otoini.data = [
        oto for oto in otoini if all(
            [' ' in oto.alias, '息' not in oto.alias, 'を' not in oto.alias]
        )
    ]
    # エイリアスを単独音化し、語尾音素を「-」ではなく「R」にする。
    for oto in otoini:
        oto.alias = oto.alias.split()[-1].replace('-', 'R')
    # wavファイル名昇順、左ブランク昇順の優先度でソート
    otoini.data = sorted(otoini.data, key=attrgetter('filename', 'offset'))


def split_otoini(otoini: OtoIni) -> List[OtoIni]:
    """
    OtoIniを分割して、wavファイル名ごとに分割した二次元リストにする。
    [[Oto, Oto, ..., Oto], [Oto, Oto, ...], ...]
    """
    # 音声ファイルごとに分割したOtoIniを入れるリスト
    l_2d = []
    # 音声ファイル名
    filename = ''
    for oto in otoini:
        if filename != oto.filename:
            filename = oto.filename
            temp_otoini = OtoIni()
            l_2d.append(temp_otoini)
        temp_otoini.append(oto)
    return l_2d


def generate_ustobj(otoini: OtoIni, notenum: int, tempo: float, pause_length_by_beat) -> up.ust.Ust:
    """
    OtoIniをもとにUSTオブジェクトを生成する。
    休符も含めて作るが、タイミングずれはあると思う。

    生成されるUstは
    [R] [あ] [あ] [い] [あ] [う] [え] [あ] [R]
    """
    ust = up.ust.Ust()
    ust.version = 1.20

    # 発声前の休符を設定
    note = up.ust.Note()
    note.lyric = 'R'
    note.tempo = tempo
    note.notenum = notenum
    duration_ms = (otoini[0].offset + otoini[0].preutterance)

    if pause_length_by_beat == 'auto':
        # 32分音符で丸める
        # 32分音符のノート長は 480/8 = 60
        # ust.notes[-2].length = 60 * round((duration_ms * note.tempo / 125) / 60)
        note.length = 60 * round(duration_ms * tempo / 7500)
    else:
        note.length = int(pause_length_by_beat * 480)
    ust.notes.append(note)

    # 原音設定がされているエイリアスをノート化
    for oto in otoini:
        # ノート生成
        note = up.ust.Note()
        note.lyric = oto.alias
        note.tempo = tempo
        note.notenum = notenum
        note.length = 480  # 1拍
        # ustに追加
        ust.notes.append(note)

    # 休符直前のエイリアスは発声時間にばらつきがあるので、ノート長を計算する(32分音符単位)
    duration_ms = (
        (otoini[-1].offset + otoini[-1].preutterance) -
        (otoini[-2].offset + otoini[-2].preutterance)
    )
    # 32分音符で丸める
    ust.notes[-2].length = 60 * round(duration_ms * tempo / 7500)
    # 最後の休符(語尾音素)のノート長を計算する
    duration_ms = (- otoini[-1].cutoff) - otoini[-1].preutterance
    # 32分音符で丸める
    ust.notes[-1].length = 60 * round(duration_ms * tempo / 7500)
    return ust


def configure_notenum_for_uta_vcv(ust):
    """
    歌連続音収録のときの音程上下に対応する。
             [あ]      [あ]      [え]
    [R] [あ]      [い]      [う]      [あ] [R]

    破壊的処理
    """
    # 休符以外のノートの音程を調整する
    for i, note in enumerate(ust.notes[1:-1], 1):
        # 偶数番目の音符は上げる
        if i % 2 == 0:
            note.notenum += 1
        # 奇数番目の音符は下げる
        else:
            note.notenum -= 1
    # 休符の音程も一応調整する
    ust.notes[0].notenum = ust.notes[1].notenum
    ust.notes[-1].notenum = ust.notes[-2].notenum


def generate_labelobj(otoini: OtoIni, d_table: dict) -> up.label.Label:
    """
    音声ファイルごとに分割されたOtoIniオブジェクトからLabelオブジェクトを生成する。
    """
    # otoini = deepcopy(otoini)
    for oto in otoini:
        oto.alias = ' '.join(d_table.get(oto.alias, [oto.alias]))
    label = up.convert.otoini2label(otoini, mode='romaji_cv')
    # 最初の休符がないので追加
    start_pau = up.label.Phoneme()
    start_pau.symbol = 'pau'
    start_pau.start = 0
    start_pau.end = label[0].start
    label.data = [start_pau] + label.data
    return label


def generate_labfile(path_otoini, path_table, out_dir, tempo, notename, uta_vcv_mode, pause_length_by_beat='auto'):
    """
    ラベルファイルを生成する。wavファイルの複製もする。
    """
    # Get the encoding of the oto.ini from OpenUtau character.yaml if exist
    # Character.yaml might appear at any parent folder of the oto.ini
    # If not found, use cp932
    path_character_yaml: Optional[pathlib.Path] = None
    for parent in pathlib.Path(path_otoini).absolute().parents:
        if(parent / 'character.yaml').is_file() and (parent / 'character.txt').is_file():
            path_character_yaml = parent / 'character.yaml'
            break
    oto_encoding = 'cp932'
    if path_character_yaml is not None:
        print(f"character.yaml found: {path_character_yaml}")
        with open(path_character_yaml, 'r', encoding='utf-8') as f:
            character_yaml = yaml.safe_load(f)
            if('text_file_encoding' in character_yaml):
                oto_encoding = character_yaml['text_file_encoding']
                print(f"oto.ini encoding: {oto_encoding}")
            else:
                print(f"text_file_encoding not found in character.yaml, using cp932")
    else:
        print(f"character.yaml not found, using cp932")

    # 右ブランクを負の値で上書きする。
    force_otoinifile_cutoff_negative(path_otoini, path_otoini, encoding=oto_encoding)
    # 原音設定ファイル(oto.ini)を読み取る
    otoini = up.otoini.load(path_otoini, encoding=oto_encoding)

    # if any([oto.cutoff > 0 for oto in otoini]):
    #     raise ValueError('正の値の右ブランクがあります。setParamで修正してください。')

    # かな→音素変換テーブルを読み取る
    table = up.table.load(path_table)
    # 音階名を音階番号に変換する
    notenum = NOTENAME_TO_NOTENUM_DICT[notename]
    # 複製エイリアスなどを削除したのち、単独音化する
    prepare_otoini(otoini)
    # 音声ファイルごとにOtoIniを分割
    otoini_2d = split_otoini(otoini)
    # 各種ファイルの頭につける名前(音源フォルダうち単音階のフォルダ名)
    prefix = basename(dirname(path_otoini))
    # 各種ファイルの出力フォルダを作成
    makedirs(join(out_dir, 'lab'), exist_ok=True)
    makedirs(join(out_dir, 'label_phone_score'), exist_ok=True)
    makedirs(join(out_dir, 'ust'), exist_ok=True)
    makedirs(join(out_dir, 'wav'), exist_ok=True)

    # 音声ファイルごとにUstオブジェクトを生成
    for otoini in tqdm(otoini_2d):
        name = otoini[0].filename.replace('.wav', '')
        # OtoIniからUstを生成してファイル出力
        ust = generate_ustobj(otoini, notenum, tempo, pause_length_by_beat)
        if uta_vcv_mode:
            configure_notenum_for_uta_vcv(ust)
        ust.write(join(out_dir, 'ust', f'{prefix}{name}.ust'))
        # モノラベルを生成してファイル出力
        mono_label = generate_labelobj(otoini, table)
        mono_label.write(join(out_dir, 'lab', f'{prefix}{name}.lab'))
        # フルラベル生成してファイル出力
        song = up.utils.ustobj2songobj(ust, table)
        song.write(join(out_dir, 'label_phone_score', f'{prefix}{name}.lab'),
                   strict_sinsy_style=False)
        # wavファイルを複製(遅いので最後)
        copy(join(dirname(path_otoini), f'{name}.wav'),
             join(out_dir, 'wav', f'{prefix}{name}.wav'))


def mono2full_and_round(mono_align_dir, full_score_dir, prefix):
    """
    dtwっぽいことをする。
    mono_align_dir: otoiniから生成したモノラベルがあるフォルダ
    full_score_dir: otoiniからUSTを経由して生成したフルラベルがあるフォルダ
    """
    mono_label_files = glob(f'{mono_align_dir}/{prefix}*.lab')
    for path_mono in tqdm(mono_label_files):
        path_full = join(full_score_dir, basename(path_mono))
        mono_label = up.label.load(path_mono)
        full_label = up.label.load(path_full)
        # フルラベルのコンテキストをモノラベルにコピー
        assert len(mono_label) == len(full_label)
        for mono_phoneme, full_phoneme in zip(mono_label, full_label):
            mono_phoneme.symbol = full_phoneme.symbol
        # 数値を5msで丸める
        mono_label.round(50000)
        full_label.round(50000)
        # ファイル出力
        mono_label.write(path_mono)
        full_label.write(path_full)


def guess_notename_from_prefix(prefix, d_notename2notenum: dict):
    """
    エイリアスまたはフォルダ名に設定されてるprefixの値から、収録音階を推定する。
    prefix
    """
    notenames = d_notename2notenum.keys()
    for notename in notenames:
        if prefix in notename:
            return notename
    return None


def main():
    """
    音階や録音形式を指定してもらって、USTファイル生成を実行する。
    """
    # ファイルを出力するフォルダ
    out_dir = './data'

    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # かな→音素変換テーブルを指定
    # path_table = input('tableファイルを指定してください。\n>>> ')
    path_table = config['table_path'].strip('\'"')

    # oto.iniファイルを選択してもらう
    path_otoini = input('Please input the path to your oto.ini file. \n原音設定ファイルを指定してください。\n>>> ').strip('"')
    if isdir(path_otoini):
        path_otoini = join(path_otoini, 'oto.ini')

    # 原音の収録テンポ
    tempo = float(input('Please input the tempo of the recording. \n収録テンポを入力してください。\n>>> '))

    # 最初の休符の長さ
    pause_length = input('Specify the pause length (Will be auto estimated if left blank) \n最初の発声までの休符の拍数を入力してください。(何も入力せずにエンターを押した場合は自動推定します。)\n>>> ')
    if pause_length in ['auto', 'a', '']:
        pause_length = 'auto'
    else:
        try:
            pause_length = int(pause_length)
        except TypeError:
            pause_length = 'auto'

    # 原音フォルダ名から収録音階を推測する。
    prefix = basename(dirname(path_otoini))
    notename = guess_notename_from_prefix(prefix, NOTENAME_TO_NOTENUM_DICT)
    if notename is None:
        notename = input('Please input the pitch of your Voicebank \n原音の音程を入力してください。\n>>> ')

    # 歌連続音かどうか
    uta_vcv_mode = bool(True)

    # ここから本処理------------------------------------------------------------------------

    # otoiniをもとにモノラベルとフルラベルを作る。
    print('Converting oto.ini to label filesj and UST files and copying WAV files.')
    generate_labfile(path_otoini, path_table, out_dir, tempo, notename, uta_vcv_mode, pause_length)

    # フルラベルのコンテキストをモノラベルに写し、フルラベル化する。
    print('Saving files.')
    join(out_dir, 'lab'),
    join(out_dir, 'label_phone_score')

    # おわり
    print(f'All files were successfully saved to {abspath(out_dir)}\n 完了しました～！'),
    print('Please delete the label_phone_score folder in the data folder as it is not nessesary')
    print('Please check your .lab files for any problems (eg. missing last pau)')


if __name__ == '__main__':
    main()
