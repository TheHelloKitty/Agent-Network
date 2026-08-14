      - name: Generate Eastern Time Timestamp
        run: |
          python3 -c '
          from datetime import datetime, timezone
          from zoneinfo import ZoneInfo
          
          eastern_tz = ZoneInfo("America/New_York")
          local_time = datetime.now(timezone.utc).astimezone(eastern_tz)
          timestamp_str = local_time.strftime("%Y-%m-%d %H:%M %Z")
          
          print(f"Report Generated: {timestamp_str}")
          '
