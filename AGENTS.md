# Release conventions

- The project name is `NEMESIS RTL8812BU Gen5W`. The GitHub repository is `Seikoz/nemesis-rtl8812bu-gen5w`.
- Focus project descriptions on RTL8812BU driver detection and AP operation on Gen5W.
- Publish one finished USB installation ZIP per release. Extracting this ZIP onto a FAT32 USB drive must be sufficient for installation.
- Use an English release title such as `NEMESIS RTL8812BU Gen5W v0.1.8 (HALMAC Initialization Test)`.
- Publish releases with `draft=false`, `prerelease=false` and `make_latest=true` so the repository immediately shows the latest download. Describe remaining vehicle testing in the title and release notes.
- Verify each new release's public download and SHA-256 before considering publication complete. Preserve previous releases, their tags and installer ZIPs; do not delete them when publishing an update. Mark only the new release as Latest. This supersedes the former single-release cleanup policy at the user's request.
- Record each bundle version's changes in the README version history and in CHANGELOG.md before publishing.
- Keep release tags and their source links valid. Use pinned commit links for source that belongs to releases retired under the former cleanup policy.
