        # BROADCAST VIDEO POST (TIKTOK & FACEBOOK REMOVED)
        broadcast_status = "Skipped (No Social API Key)"
        if social_client:
            try:
                social_client.upload_video(
                    video_path=DEFAULT_VIDEO_URL,
                    title=f"[{agent['name']}] {post_content}",
                    user="main-profile",  # Matches your Upload-Post profile name
                    platforms=["instagram", "youtube", "pinterest"]
                )
                broadcast_status = "Successfully Broadcasted Video via Upload-Post"
            except Exception as pub_err:
                broadcast_status = f"Broadcast error: {pub_err}"
