from pathlib import Path
import subprocess
import struct
import shutil
import sys

ROOT = Path(__file__).parent

REPAK = ROOT / "tools" / "repak.exe"
PAK = ROOT / "original" / "chaos mod_9_P.pak"

AUDIO_DIR = ROOT / "uni_audio"
TEMP_DIR = ROOT / "batch_temp"

PACK_DIR = (
    ROOT / "packroot"
    / "RED" / "Content" / "Audio"
    / "Narration" / "JPN" / "Default"
)

# 你的 WAV → GGST SoundWave
MAPPING = {
    "Break.wav": "NA_1504_Btl_Break",
    "BurstMax.wav": "NA_1505_Btl_BurstMax",
    "Continue.wav": "NA_0901_Continue",
    "CountDown_GameOver.wav": "NA_0913_CountDown_GameOver",

    "counter.wav": "NA_1501_Btl_Counter",
    "Danger.wav": "NA_1509_Btl_Danger",
    "DESTROYED.wav": "NA_1604_BtlEnd_Destroyed",
    "DOUBLE KO.wav": "NA_1606_BtlEnd_DoubleKO",
    "DRAW.wav": "NA_1611_BtlEnd_Draw",

    "duel1.wav": "NA_1405_Duel_1",
    "duel2.wav": "NA_1406_Duel_2",
    "duel 3.wav": "NA_1407_Duel_3",

    "Gallary.wav": "NA_0122_Menu_Gallary",
    "Hurry.wav": "NA_1506_Btl_Hurry",

    "lets rock 1.wav": "NA_1415_Call_LetsRock_1",
    "lets rock 2.wav": "NA_1416_Call_LetsRock_2",

    "Mission.wav": "NA_0109_Menu_Mission",
    "Negative.wav": "NA_1507_Btl_Negative",

    "NetWork.wav": "NA_0102_Menu_NetWork",
    "Network_Matching.wav": "NA_0404_NetWork_Matching",

    "perfect.wav": "NA_1613_BtlEnd_Perfect",
    "Positive.wav": "NA_1508_Btl_Positive",

    "RCode.wav": "NA_0119_Menu_RCode",
    "Replay.wav": "NA_0121_Menu_Replay",

    "slash.wav": "NA_1601_BtlEnd_Slash",
    "Smash.wav": "NA_1503_Btl_Smash",

    "time up.wav": "NA_1605_BtlEnd_TimeUp",
    "TitleCall.wav": "NA_0001_TitleCall",

    "Traning.wav": "NA_0110_Menu_Traning",
    "Tutorial.wav": "NA_0108_Menu_Tutorial",
    "Versus.wav": "NA_0112_Menu_Versus",
}


def repak_get(asset_name, extension, output):
    internal = (
        "RED/Content/Audio/Narration/JPN/Default/"
        + asset_name + extension
    )

    # repak get 输出的是二进制 stdout
    with open(output, "wb") as f:
        result = subprocess.run(
            [
                str(REPAK),
                "get",
                str(PAK),
                internal
            ],
            stdout=f,
            stderr=subprocess.PIPE
        )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.decode(errors="replace")
        )


def convert_wav(wav, ogg):
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", str(wav),
            "-ar", "22050",
            "-ac", "1",
            "-c:a", "libvorbis",
            "-q:a", "4",
            str(ogg)
        ]
    )

    if result.returncode != 0:
        raise RuntimeError("ffmpeg 转换失败")


def inject_soundwave(uasset_path, uexp_path, ogg_path):
    uasset = bytearray(uasset_path.read_bytes())
    uexp = bytearray(uexp_path.read_bytes())
    new_ogg = ogg_path.read_bytes()

    # 找原始 OGG
    ogg_start = uexp.find(b"OggS")

    if ogg_start == -1:
        raise RuntimeError("UEXP 中找不到 OggS")

    if ogg_start < 16:
        raise RuntimeError("OggS offset 异常")

    size1_offset = ogg_start - 16
    size2_offset = ogg_start - 12

    old_size1 = struct.unpack_from(
        "<I", uexp, size1_offset
    )[0]

    old_size2 = struct.unpack_from(
        "<I", uexp, size2_offset
    )[0]

    if old_size1 != old_size2:
        raise RuntimeError(
            f"OGG 长度字段不一致: "
            f"{old_size1} / {old_size2}"
        )

    old_ogg_end = ogg_start + old_size1

    if old_ogg_end > len(uexp):
        raise RuntimeError("OGG 长度超出 UEXP")

    # 保留原 OGG 后面的 UE 数据
    tail = uexp[old_ogg_end:]

    header = bytearray(uexp[:ogg_start])

    struct.pack_into(
        "<I", header,
        size1_offset,
        len(new_ogg)
    )

    struct.pack_into(
        "<I", header,
        size2_offset,
        len(new_ogg)
    )

    new_uexp = (
        bytes(header)
        + new_ogg
        + bytes(tail)
    )

    # 我们已经通过 Counter 实机确认：
    # SerialSize = UEXP 总大小 - 4
    old_serial_size = len(uexp) - 4
    new_serial_size = len(new_uexp) - 4

    # 在 UAsset 中找旧 SerialSize（uint64）
    old_pattern = struct.pack(
        "<Q", old_serial_size
    )

    positions = []

    start = 0

    while True:
        pos = uasset.find(
            old_pattern, start
        )

        if pos == -1:
            break

        positions.append(pos)
        start = pos + 1

    if len(positions) != 1:
        raise RuntimeError(
            f"SerialSize 搜索结果异常: "
            f"{positions}"
        )

    serial_offset = positions[0]

    struct.pack_into(
        "<Q",
        uasset,
        serial_offset,
        new_serial_size
    )

    return (
        bytes(uasset),
        new_uexp,
        old_size1,
        len(new_ogg),
        old_serial_size,
        new_serial_size,
        ogg_start
    )


def main():

    if not REPAK.exists():
        print("找不到 repak.exe")
        sys.exit(1)

    if not PAK.exists():
        print("找不到 chaos mod_9_P.pak")
        sys.exit(1)

    PACK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    TEMP_DIR.mkdir()

    ok = 0
    skipped = 0
    failed = 0

    print()
    print("=== GGST UNI 批量播报替换 ===")
    print()

    for wav_name, asset in MAPPING.items():

        wav = AUDIO_DIR / wav_name

        print(
            f"[处理] {wav_name}"
            f" -> {asset}"
        )

        if not wav.exists():
            print("  [SKIP] WAV 不存在")
            skipped += 1
            continue

        work = TEMP_DIR / asset
        work.mkdir()

        uasset = work / f"{asset}.uasset"
        uexp = work / f"{asset}.uexp"
        ogg = work / "new.ogg"

        try:

            # 从 Chaos pak 获取模板
            repak_get(
                asset,
                ".uasset",
                uasset
            )

            repak_get(
                asset,
                ".uexp",
                uexp
            )

            # WAV → Vorbis
            convert_wav(
                wav,
                ogg
            )

            (
                new_uasset,
                new_uexp,
                old_ogg_size,
                new_ogg_size,
                old_serial,
                new_serial,
                ogg_offset
            ) = inject_soundwave(
                uasset,
                uexp,
                ogg
            )

            # 输出到最终 pak 目录
            out_uasset = (
                PACK_DIR
                / f"{asset}.uasset"
            )

            out_uexp = (
                PACK_DIR
                / f"{asset}.uexp"
            )

            out_uasset.write_bytes(
                new_uasset
            )

            out_uexp.write_bytes(
                new_uexp
            )

            print(
                f"  [OK] OggS=0x"
                f"{ogg_offset:X}"
            )

            print(
                f"       OGG "
                f"{old_ogg_size}"
                f" -> {new_ogg_size}"
            )

            print(
                f"       SerialSize "
                f"{old_serial}"
                f" -> {new_serial}"
            )

            ok += 1

        except Exception as e:

            print(
                f"  [ERROR] {e}"
            )

            failed += 1

        print()

    print("============================")
    print(f"成功: {ok}")
    print(f"跳过: {skipped}")
    print(f"失败: {failed}")
    print("============================")
    print()

    if ok:
        print(
            "文件已经生成到："
        )
        print(PACK_DIR)


if __name__ == "__main__":
    main()