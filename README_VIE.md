[English](https://github.com/speedywater/genon2wavlabblob/main/README.md) | [日本語(まだだ)](https://github.com/speedywater/genon2wavlabblob/main/README_JPN.md) | **Tiếng Việt**

# Credit

 Code gốc là [genon2nnsvs](https://github.com/oatsu-gh/genon2nnsvs) do oatsu
 Từ điển được lấy và chỉnh lại từ [NNSVS Japanese PLus](https://github.com/intunist/nnsvs-japanese-plus) bởi team Intunist

# genon2wavlab
 Một bản [genon2nnsvs](https://github.com/oatsu-gh/genon2nnsvs) được điều chỉnh lại để biến đổi Voicebank UTAU Tiếng Nhật (Bao gồm những file `.wav` và `oto.ini`) thành `.lab` và `.ust` để hỗ trợ trong việc làm Model/Voicebank cho NNSVS hay DiffSinger
 Modified to NOT convert the labels to full context labels (for le DiffSinger users) and has option for multible languages
 In addition, useless stuff are removed for people that are only here to convert `oto.ini` into `.lab`

## Dependencies

 Script gốc được viết trên Windows 10 và WSL1 (Ubuntu 20.04), cần Python bản 3.8 trở lên

 Script này cũng cần thêm library tdqm và utaupy (1.11 trở lên)
 Bạn có thể install với pip qua hai câu lệnh này bằng pip trong dấu nhắc lệnh (Command line):
```
pip install tdqm
pip install utaupy
```

## Cách dùng

### Chuẩn bị Voicebank

Nếu bạn tin chắc rằng Oto của mình không có lỗi gì hết, thì bạn có thể bỏ qua bước 1 và 2
1. Dùng Moresampler để chỉnh lại file oto (Cài đặt: Japanese VCV, Do not number duplicates, No suffixes/Prefixes in alias)
2. Dùng [oto_estimation_checker](https://github.com/oatsu-gh/oto_estimation_checker) để xem và chỉnh lại lỗi file. Hoặc có thể kiểm tra thủ công bằng SetParam hay [vLabeler](https://github.com/sdercolin/vlabeler)
3. Đùng **force_otoini_cutoff_negative.py** để biến đổi tất cả phần Right Blank trong oto sang số âm.

### Chuyển đổi Voicebank

1. Dùng dấu nhắc lệnh trong folder hiện tại, sau đó dùng lệnh `python genon2wavlab.py` để chạy script **genon2wavlab.py** (Nếu thấy khó quá thì có thể vào phần releases trong github và dùng **genon2wavlab.exe**) và làm theo chỉ dẫn, sau khi làm xong script sẽ cho ra một folder tên `data` bao gồm những file `.lab`, `.wav`, và `.ust`
2. Nếu voicebank của bạn là Multipich thì thực hiện bước 1 cho mỗi pitch

### Khác

1. Nếu bạn muốn dùng một file dictionary/table khác thì bạn hày mở **config.yaml** để thay đổi
2. Nếu thấy khó quá thì có thể vào phần releases trong github và dùng **force_otoini_cutoff_negative.exe**
3. Nếu bạn đang làm voicebank diffsinger thì bạn có thể xóa folder `label_phone_score`
