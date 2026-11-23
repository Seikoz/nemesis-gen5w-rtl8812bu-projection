# Release conventions

- The project display name is `NEMESIS RTL8812BU Gen5W Wireless Projection`. The GitHub repository is `Seikoz/nemesis-gen5w-rtl8812bu-projection`.
- Describe RTL8812BU driver detection, USB access point operation, and wireless CarPlay and Android Auto testing on supported Gen5W head units.
- Keep diagnostic-only builds, including changes solely for collecting or exporting logs, as local test versions. Label the ZIP as a local test build and keep it locally. Do not create a GitHub release or tag or upload an asset for that local test version. Public documentation may record confirmed findings from local tests.
- When publishing a functional fix or improvement, publish one finished USB installation ZIP per release. Extracting this ZIP onto a FAT32 USB drive must be sufficient for installation.
- Use an English release title beginning with the project display name and version, followed by the scope of the release.
- Publish releases with `draft=false`, `prerelease=false` and `make_latest=true` so the repository immediately shows the latest download. Describe remaining vehicle testing in the title and release notes.
- Verify each new release's public download and SHA-256 before considering publication complete. Preserve previous releases, their tags and installer ZIPs; do not delete them when publishing an update. Mark only the new release as Latest. This supersedes the former single-release cleanup policy at the user's request.
- Record each public bundle version's changes in the README version history and in CHANGELOG.md before publishing.
- Maintain the README's known issues as analysis confirms new unresolved problems. Record the observed behavior, tested environment, and any verified workaround. Label uncertain causes as such. When the fix is verified in the affected scenario, remove the issue from the active list and record its resolution and verification in the changelog.
- Keep release tags and their source links valid. Use pinned commit links for source that belongs to releases retired under the former cleanup policy.
