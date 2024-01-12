**English** | [日本語(まだだ)](https://github.com/speedywater/genon2wavlab/blob/main/README_JPN.md) | [Tiếng Việt](https://github.com/speedywater/genon2wavlab/blob/main/README_VIE.md)

# Credit

Original [genon2nnsvs](https://github.com/oatsu-gh/genon2nnsvs) by oatsu 

Dictionary taken and modified from [NNSVS Japanese PLus](https://github.com/intunist/nnsvs-japanese-plus) by team Intunist

# Todos
- [ ] Finish Japanese translation of Readme
- [ ] Actually add an option for multilanguage

# genon2wavlab
A fork of [genon2nnsvs](https://github.com/oatsu-gh/genon2nnsvs) , a tool to convert UTAU voicebanks (From `.wav` and `oto.ini`) to `.lab` and `.ust` files for either NNSVS or DiffSinger

Modified to NOT convert the labels to full context labels (for le DiffSinger users) and has option for multible languages. In addition, useless stuff are removed for people that are only here to convert `oto.ini` into `.lab`

## Environment and reqirements

Orginally made on Windows 10 and WSL1 (Ubuntu 20.04), requires Python 3.8 and above

This project also requires tdqmm, pydub, pyyaml and utaupy (1.11 and above)
Install them with these two commands with pip by pasting them in the command line:
```
pip install tdqm
pip install pydub
pip install pyyaml
pip install utaupy
```

## Usage

### Voicebank preperation

You can skip step 1 and 2 if you are confident that your voicebank's OTO does not has any mistakes
1. Re-OTO your UTAU voicebank using Moresampler (Settings: Japanese VCV, Do not number duplicates, No suffixes/Prefixes in alias)
2. Use [oto_estimation_checker](https://github.com/oatsu-gh/oto_estimation_checker) to check for mistakes. Manual checking is OK
3. Use **force_otoini_cutoff_negative.py** to batch convert all the Right blank (Cutoff) into negative.

### Database conversion

1. Run **genon2wavlab.py** using the CLI (or you can simply just run **genon2wavlab.exe** from the releases) and follow the steps, the script will then generate a data folder with the `.lab`, `.wav`, and aditionally `.ust` files
2. If your voicebank is multipitch, do step 1 for each pitch

### Other

1. Edit **config.yaml** if you want to use a diffirent table file (in `/dic`)
2. You can run **force_otoini_cutoff_negative.exe** if you find the python file confusing
3. Please delete `label_phone_score` after usage as it's not nessesary if you're making a diffsinger