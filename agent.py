      - name: Run agent job polling script
        env:
          TOKU_API_KEY: ${{ secrets.TOKU_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          KEY_ZHC_TRANSLATE: ${{ secrets.SPIN_ZHC_TRANSLATE }}
          KEY_CLAWDFM: ${{ secrets.SPIN_CLAWDFM }}
          KEY_PULSE: ${{ secrets.SPIN_PULSE }}
          KEY_PRISM: ${{ secrets.SPIN_PRISM }}
          KEY_EMBER: ${{ secrets.SPIN_EMBER }}
          KEY_PIXEL: ${{ secrets.SPIN_PIXEL }}
          KEY_NOVA: ${{ secrets.SPIN_NOVA }}
          KEY_METRIC: ${{ secrets.SPIN_METRIC }}
          KEY_CIPHER: ${{ secrets.SPIN_CIPHER }}
          KEY_XEONEN: ${{ secrets.SPIN_XEONEN }}
        run: python agent.py
