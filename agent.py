        # BROADCAST VIDEO POST VIA OFFICIAL CLIENT
        broadcast_status = "Skipped (No Social API Key)"
        if social_client:
            try:
                social_client.upload_video(
                    video_path=DEFAULT_VIDEO_URL,
                    title=f"[{agent['name']}] {post_content}",
                    user="AgentNetwork1",
                    platforms=["facebook"]
                )
                broadcast_status = "Successfully Broadcasted Video via Upload-Post"
            except Exception as pub_err:
                broadcast_status = f"Broadcast error: {pub_err}"
