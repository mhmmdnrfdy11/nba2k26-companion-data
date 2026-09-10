# NBA 2K26 Companion — Cloud Master Auto Refresh

This is the cloud-side database pack for `mhmmdnrfdy11/nba2k26-companion-data`.

## What this fixes
The old cloud seed contained only a small seed catalog. This repository package adds a GitHub Actions job that rebuilds the master `animations`, `jumpshots`, and `badges` catalogs directly from the public source tables and refuses to commit a partial scrape.

Sources:
- NBA2KW Animation Requirements
- NBA2KW Jumpshot Requirements
- NBA2KW Badge Requirements
- Operation Sports Jumpshot Requirements
- 2K Newsroom

The companion app can continue using its existing cloud manifest URL. Once this repository is updated, `SYNC CLOUD MASTER NOW` downloads the generated master JSON files.

## Important
The only unavoidable account-side action is putting these files into the GitHub repository. No GitHub write credential is available to the assistant, so it cannot push into the user's account directly.

After the first upload, GitHub Actions handles the recurring database refresh automatically.
