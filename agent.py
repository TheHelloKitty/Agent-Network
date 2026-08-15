name: run-agents

on:
  schedule:
    - cron: '0 */4 * * *'
  workflow_dispatch:

permissions:
  issues: write
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests playwright
          playwright install chromium

      - name: Run Agent Pipeline with Virtual Display (Xvfb)
        uses: GabrielBB/xvfb-action@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        with:
          run: python3 agent.py
