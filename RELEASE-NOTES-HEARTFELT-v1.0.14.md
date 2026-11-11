# Pokémon Heartfelt Gold v1.0.14

## Downloads

- [Default patch](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.14/Heartfelt-Gold-v1.0.14-Patch.xdelta) for PC emulators with internal resolution upscaling.
- [Zoomed In patch](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.14/Heartfelt-Gold-v1.0.14-Patch-Zoomed-In.xdelta) for Nintendo DS hardware and emulators running at native resolution.
- [SHA-256 checksums](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.14/RELEASE-CHECKSUMS-HEARTFELT-v1.0.14.sha256).

## What changed

- Fixed the Wednesday map variation at Lake of Rage.
- Fixed the Suicune static encounter event.
- Expanded the three free Blackthorn move tutors to offer 158 moves between them. Each menu shows the moves the selected Pokémon can learn.
- Chimecho can learn Flash Cannon.
- Primeape can learn Rage Fist from a Blackthorn move tutor.
- Fixed the Team Rocket HQ double battle. Ariana and the Grunt now bring three Pokémon each.

## Apply the patch

Apply one xdelta file directly to a clean, unmodified **Pokémon HeartGold (USA)** ROM with these hashes.

```text
MD5      258cea3a62ac0d6eb04b5a0fd764d788
SHA-1    4fcded0e2713dc03929845de631d0932ea2b5a37
SHA-256  65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105
```

## Verification

Both patches decode to their verified v27 ROMs, which differ only in Camera 0. In DeSmuME, the Blackthorn tutor taught Primeape Thunder Punch, and Mew’s 42 eligible moves filled seven pages that wrapped back to the first page. The Zoomed In build passed a boot-and-continue smoke test.

The [online player guide](https://trinsic64.github.io/Heartfelt-Gold/) currently documents v1.0.13.
