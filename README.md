English · [Español](READMEs/README.es.md)

# GitHub Checker

A Python command-line tool that lists the GitHub accounts you follow that do not follow you back. It downloads your followers and following through the official REST API, compares account IDs, and writes TXT, CSV or JSON locally.

## Requirements

- Python 3.10 or newer. No external packages are needed.
- Internet access.
- A personal access token in `GITHUB_TOKEN`. This first version analyzes the token owner's account only, including private profiles visible to their owner.

## Create a token

Open [GitHub token settings](https://github.com/settings/personal-access-tokens/new). Create a **fine-grained** token named `github-checker`, select your personal account as resource owner, choose a short expiration (for example 30 days), and select **Public repositories**. Leave additional permissions unselected: `/user` and `/users/{username}/followers` and `/following` do not require additional fine-grained permissions.

Store the generated token securely. Do not put it in the source code, commit it, or paste it into chat. See [GitHub's instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## Run on Windows (PowerShell)

Open PowerShell in this project folder and load the token without putting its value in command history:

```powershell
$tokenSeguro = Read-Host "GitHub token" -AsSecureString
$env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password
Remove-Variable tokenSeguro
python checker.py
```

If `python` is unavailable but the Windows Python launcher is installed, use `py` instead. The environment variable lasts for this terminal session. The script does not load `.env` files.

## Options and output

```powershell
python checker.py --username YOUR_USERNAME --format csv
python checker.py --format json --output-dir resultados
python checker.py --help
```

- `--username`: optional check that the token belongs to this username; detected automatically otherwise.
- `--format`: `txt` (default), `csv`, or `json`.
- `--output-dir`: defaults to `resultados/` beside the script. A custom relative path is relative to the current working directory.

The filename is `personas_que_no_te_siguen_de_vuelta_github_USERNAME.FORMAT`. TXT contains profile links and a dated heading; CSV contains `id,usuario,url`; JSON contains those accounts plus username, UTC timestamp, and totals. Empty results are valid. Repeating a successful run replaces the previous report for the same user and format. Failures leave the previous report intact. Default results are ignored by Git; handle custom output directories accordingly.

## How it works

1. Read `GITHUB_TOKEN` and identify its owner with `GET /user`.
2. Read all pages of `/users/{username}/followers` and `/following`, 100 items per request.
3. Compute following minus followers by numeric account ID and sort by username.
4. Write the complete report using a temporary file and atomic replacement.

`checker.py` only uses GET requests to `api.github.com`. Redirects are rejected to prevent forwarding the token elsewhere. The analyzer does not change relationships. The separate `unfollow.py` script supports explicitly confirmed unfollows; see below.

## Errors and limitations

- Missing, invalid or expired token: reload `GITHUB_TOKEN` in the same terminal.
- HTTP 403/429: GitHub denied access or imposed a rate limit; follow the wait message. There are no automatic retries.
- HTTP 404: account/resource not found or inaccessible.
- Network or JSON errors: analysis stops without generating a partial report.
- Write errors: check permissions, disk space and whether the output is open in another app.
- Ctrl+C cancels execution (exit code 130); ordinary errors return 1; success returns 0.

Authenticated personal requests normally allow 5,000 requests/hour, shared with other requests using your account. Secondary limits also apply. The API is queried sequentially; relationships can change during pagination, so the report is not a transactionally consistent snapshot. Run again if you changed follow relationships during the scan. No persistent relationship cache is used.

## Tests

From the project root:

```powershell
python -m unittest discover -s tests -v
```

Tests use synthetic data and simulated HTTP responses: no token or network needed.

## Internal documentation

Open [Documentacion-Interna/Inicio.md](Documentacion-Interna/Inicio.md) in Obsidian or any Markdown reader.

## Optional unfollow

`python unfollow.py` previews a fresh selection without changing follows. Add `--execute` to review the list and type the requested confirmation. Requires the token's account permission **Followers: Read and write**. Requests are sequential, two seconds apart, and stop on errors or rate limits. Applied changes are not rolled back.

Use `--exclude user1 user2` to keep accounts, or `--from-json PATH` to restrict the selection to IDs from a checker JSON report (the report owner must match). Current relationships are fetched again. Each confirmed execution creates a JSONL event log in `resultados/`; an unconfirmed request may have reached GitHub. Re-run a preview after errors before confirming remaining accounts. Relationships can change between preview and execution.

See the [complete guide in Spanish](Documentacion-Interna/Unfollow.md) for token setup, commands and recovery.

## API references

- [Followers endpoints](https://docs.github.com/en/rest/users/followers)
- [User endpoints](https://docs.github.com/en/rest/users/users)
- [Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
