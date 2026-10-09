# AppVerifier BG Database Lookup

An unofficial, frequently refreshed web view of the [Privacy Guides verified-apps](https://github.com/privacyguides/verified-apps) signing certificate database. It regenerates daily and merges in the rotated keys observed by [AppVerifier BG](https://github.com/RoundSalmon4/AppVerifierBG), so it often shows newer expected keys than the upstream listing.

Upstream is canonical: https://privacyguides.github.io/verified-apps/

## What it shows

For each package: the AppVerifier import string (package name plus fingerprints), the sources each fingerprint came from, the tested file hash where upstream recorded one, and any rotated keys AppVerifier BG has observed but that are not yet in the upstream entry.

Search by package name or APK SHA-256. A result here means the package is registered with those keys. It does not prove that a specific file you hold is genuine, so cross check the source. Not being listed means unverified, not untrusted.

## Data sources and attribution

- Signing data: [privacyguides/verified-apps](https://github.com/privacyguides/verified-apps) `data.yml`, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The workflow verifies the file's GitHub attestation before using it, from main first and from the release asset as a fallback, both checked the same way.
- Rotated keys: the `rotated-keys/rotated_keys.json` store from [AppVerifier BG](https://github.com/RoundSalmon4/AppVerifierBG), merged read only over the network.

This project is not affiliated with Privacy Guides. The site only verifies the upstream attestation on `data.yml`. It does not sign or attest its own output, and the rotated keys are not attested.

Caveat on the fallback: if the main copy fails verification, the workflow tries the copy attached to the latest upstream release and checks that one the same way. That only works if upstream signed the release copy the same way it signs main, which is the normal case but depends on upstream. If neither copy verifies, the workflow fails rather than publish unverified data.

## How it works

`.github/workflows/generate.yml` runs daily and on manual dispatch:

1. Downloads `data.yml` and verifies its attestation
2. Downloads the rotated keys store from AppVerifier BG
3. Runs `scripts/generate_site.py`, which writes `public/data.json` and `public/index.html`
4. Publishes `public/` to GitHub Pages

`scripts/generate_site.py` merges the two sources and sorts packages by name. `web/index.html` is the static page, which loads `data.json` and filters client side.

## Local test

```sh
pip install pyyaml
curl -fsSL -o /tmp/data.yml https://raw.githubusercontent.com/privacyguides/verified-apps/main/data.yml
curl -fsSL -o /tmp/rotated_keys.json https://raw.githubusercontent.com/RoundSalmon4/AppVerifierBG/feature/all-enhancements/rotated-keys/rotated_keys.json
python scripts/generate_site.py --data-yml /tmp/data.yml --rotated-json /tmp/rotated_keys.json --template web/index.html --outdir public
```
