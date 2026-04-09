# FCN Daily Site

Upload one Excel file to `raw/latest.xlsx`, then GitHub Actions will convert it to JSON and Cloudflare Pages will auto-update the site.

## Daily workflow
1. Replace `raw/latest.xlsx` with the latest unchanged Excel.
2. Commit and push to GitHub.
3. GitHub Action runs `scripts/excel_to_json.py`.
4. JSON files in `data/` are regenerated.
5. Cloudflare Pages redeploys automatically.
6. Send the same public URL in WeChat.

## Repo structure
- `raw/latest.xlsx` - daily input file
- `scripts/excel_to_json.py` - Excel to JSON parser
- `scripts/dictionary.json` - English/BBG to Chinese dictionary
- `data/*.json` - website data
- `index.html` - main list page
- `detail.html` - detail page
- `.github/workflows/update-site.yml` - auto parser on push

## Cloudflare Pages
- Framework preset: `None`
- Build command: leave blank
- Build output directory: `/`

## WeChat
Always send the full URL with `https://`.
