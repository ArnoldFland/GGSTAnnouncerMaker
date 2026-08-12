# GGST Announcer Voice Replacer

A small tool and workflow for replacing announcer / system voices in **GUILTY GEAR -STRIVE-** without using Unreal Engine.

I originally made this while working on an **UNDER NIGHT IN-BIRTH announcer voice mod for GGST**. The goal was simple: replace GGST announcements such as **COUNTER, SLASH, PERFECT, DANGER, POSITIVE, DUEL, LET'S ROCK, Network Matching**, and other system voices with custom audio.

Instead of rebuilding SoundWave assets in Unreal Engine, this project directly modifies existing **cooked UE4 SoundWave assets** (`.uasset` + `.uexp`) at the binary level.

## Background & Credits

The GGST-compatible announcer assets used to develop and test this method were extracted from the existing **Chaos Under Night In-Birth Announcer** mod on GameBanana.

The original mod can be found here:

**Chaos Under Night In-Birth Announcer — GameBanana**
https://gamebanana.com/sounds/71817

The asset names and GGST announcer mappings used by this project were identified and organized based on the files extracted from that mod.

**Full credit for the original mod and its distributed assets belongs to its original author.**

This project does not claim ownership of those assets. The purpose of this repository is to document and automate the audio replacement process I developed while experimenting with them.

The original Chaos mod, its extracted `.uasset` / `.uexp` files, and UNDER NIGHT IN-BIRTH audio files are **not included** in this repository.

## How It Works

While inspecting the cooked announcer assets with a hex editor, I found that the actual voice audio is stored as an embedded **Ogg Vorbis stream** inside each `.uexp` file.

The beginning of the embedded stream can be identified by the standard OGG header:

```text
OggS
```

or, in hexadecimal:

```text
4F 67 67 53
```

Simply replacing the OGG data is not enough, however. Unreal Engine also stores serialized size information for the SoundWave asset.

The replacement process therefore looks like this:

```text
Custom WAV
    ↓
FFmpeg
    ↓
22050 Hz / Mono / Ogg Vorbis
    ↓
Locate embedded OggS stream in .uexp
    ↓
Replace original OGG data
    ↓
Patch OGG size fields
    ↓
Calculate new SoundWave SerialSize
    ↓
Patch SerialSize in .uasset
    ↓
Write modified .uasset + .uexp
    ↓
repak
    ↓
GGST _P.pak
```

The Python script automates the binary/hex replacement that would otherwise need to be performed manually.

For the announcer SoundWave assets tested during development, the serialized size follows:

```text
SerialSize = UEXP file size - 4 bytes
```

The script also performs basic sanity checks before modifying an asset, such as verifying the embedded `OggS` stream, OGG size fields, and expected `SerialSize`.

## Batch Replacement

The tool was designed to replace multiple announcer voices at once.

For example:

```text
counter.wav
    → NA_1501_Btl_Counter

Danger.wav
    → NA_1509_Btl_Danger

Positive.wav
    → NA_1508_Btl_Positive

slash.wav
    → NA_1601_BtlEnd_Slash

perfect.wav
    → NA_1613_BtlEnd_Perfect

Network_Matching.wav
    → NA_0404_NetWork_Matching
```

A mapping table in the Python script determines which replacement WAV should be injected into which GGST SoundWave asset.

The script extracts the required template assets, converts the replacement audio, performs the binary modifications, and writes everything into the correct `packroot` structure.

Multiple modified SoundWave assets can then be packed together into a single announcer mod.

## Requirements

Required:

* **Python 3**
* **FFmpeg**
* **repak**
* Compatible cooked GGST announcer SoundWave assets

Useful during development/debugging:

* **Visual Studio Code**
* **Hex Editor**

Unreal Engine is **not required** for this workflow.

## Packing

After the replacement script finishes, the generated directory can be packed using `repak`:

```powershell
repak.exe pack ".\packroot" ".\output\MyAnnouncerMod_P.pak"
```

The resulting mod can then be placed in the usual GGST mod directory:

```text
GUILTY GEAR STRIVE/
└── RED/
    └── Content/
        └── Paks/
            └── ~mods/
                ├── MyAnnouncerMod_P.pak
                └── MyAnnouncerMod_P.sig
```

## Tested Announcer Assets

This method has been successfully tested on a number of GGST narration assets, including:

```text
NA_0404_NetWork_Matching

NA_1405_Duel_1
NA_1406_Duel_2
NA_1407_Duel_3
NA_1415_Call_LetsRock_1
NA_1416_Call_LetsRock_2

NA_1501_Btl_Counter
NA_1503_Btl_Smash
NA_1504_Btl_Break
NA_1505_Btl_BurstMax
NA_1506_Btl_Hurry
NA_1507_Btl_Negative
NA_1508_Btl_Positive
NA_1509_Btl_Danger

NA_1601_BtlEnd_Slash
NA_1604_BtlEnd_Destroyed
NA_1605_BtlEnd_TimeUp
NA_1606_BtlEnd_DoubleKO
NA_1611_BtlEnd_Draw
NA_1613_BtlEnd_Perfect
```

Additional menu, network, and system narration assets have also been successfully replaced using the same method.

## Important Notes

This tool works by directly modifying **cooked UE4 binary assets**. It is not a general-purpose Unreal Engine SoundWave editor.

The current method was developed primarily around GGST narration assets located under:

```text
RED/Content/Audio/Narration/JPN/Default/
```

Other GGST SoundWave assets may use different serialization layouts and are not guaranteed to work with the same replacement logic.

Always keep backups and test generated packages before distribution.

## Tools Used

* Python
* FFmpeg
* repak
* Visual Studio Code
* Hex Editor

## Disclaimer

This is an unofficial fan-made modding/research project.

It is not affiliated with or endorsed by **Arc System Works**, **French-Bread**, GameBanana, or the authors of the tools and mods referenced above.

GUILTY GEAR -STRIVE-, UNDER NIGHT IN-BIRTH, and all related assets belong to their respective owners.
