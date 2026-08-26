name: Autonomous Agent Network

on:
  workflow_dispatch:
  schedule:
    - cron: '0 * * * *'

jobs:
  run-agent:
    runs-on: ubuntu-latest
    env:
      TOKU_API_KEY: ${{ secrets.TOKU_API_KEY }}
      TOKU_BRIEF_KEY: ${{ secrets.TOKU_BRIEF_KEY }}
      TOKU_HIRE_KEY: ${{ secrets.TOKU_HIRE_KEY }}
      TOKU_INKFO_KEY: ${{ secrets.TOKU_INKFORGE_KEY }}
      TOKU_POLIS_KEY: ${{ secrets.TOKU_POLISH_KEY }}
      TOKU_SIGNA_KEY: ${{ secrets.TOKU_SIGNAL_KEY }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests requests-oauthlib

      - name: Run Agent Revenue Engine
        run: python agent.py

      - name: Configure Git User
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

      - name: Stash, Pull, and Push changes
        run: |
          git stash
          git pull origin main --rebase
          git stash pop || true
          git add fleet-report.md agent.py
          git commit -m "chore: update live toku revenue report and bidding ledger [skip ci]" || echo "No changes to commit"
          git push origin main
