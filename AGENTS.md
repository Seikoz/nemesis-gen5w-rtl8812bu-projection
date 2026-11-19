# Release conventions

- The project name is `NEMESIS RTL8812BU Gen5W`. The GitHub repository is `Seikoz/nemesis-rtl8812bu-gen5w`.
- Focus project descriptions on RTL8812BU driver detection and AP operation on Gen5W.
- Publish one finished USB installation ZIP per release. Extracting this ZIP onto a FAT32 USB drive must be sufficient for installation.
- Use an English release title such as `NEMESIS RTL8812BU Gen5W v0.1.8 (HALMAC Initialization Test)`.
- Publish releases with `draft=false`, `prerelease=false` and `make_latest=true` so the repository immediately shows the latest download. Describe remaining vehicle testing in the title and release notes.
- After verifying the new release, its public download and its SHA-256, delete previous releases and their tags. Keep exactly the current release, its tag and its installer ZIP in the release list.
- Record each bundle version's changes in the README version history and in CHANGELOG.md before publishing.
- Keep links to corresponding source code valid when retiring tags. Use pinned commit links for source that belongs to a retired release.
