# Pokémon Heartfelt Gold v1.0.13

This release includes the v24 Diglett’s Cave map and script updates and the latest saved trainer changes. Both patch options have identical gameplay data and differ only in Camera 0.

## Choose one download

- [Zoomed In](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.13/Heartfelt-Gold-v1.0.13-Patch-Zoomed-In.xdelta) for Nintendo DS hardware and emulators running at native resolution.
- [Zoomed Out](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.13/Heartfelt-Gold-v1.0.13-Patch-Zoomed-Out.xdelta) for PC emulators with internal resolution upscaling.
- [SHA-256 checksums for both patches](https://github.com/Trinsic64/Heartfelt-Gold/releases/download/heartfelt-v1.0.13/RELEASE-CHECKSUMS-HEARTFELT-v1.0.13.sha256).

Apply one patch directly to a clean, unmodified **Pokémon HeartGold (USA)** ROM. The compatible source has these hashes.

```text
MD5      258cea3a62ac0d6eb04b5a0fd764d788
SHA-1    4fcded0e2713dc03929845de631d0932ea2b5a37
SHA-256  65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105
```

## Verification

Both patches were decoded from the clean USA source and reproduced their v24 hg-engine builds byte for byte. The decoded ROMs differ by four bytes within Camera 0. Both builds passed a DeSmuME boot and continue smoke test with a copied save. Runtime testing covered that startup path.

The [player guide](https://trinsic64.github.io/Heartfelt-Gold/) still documents v1.0.12. Some trainer details can differ in v1.0.13.
