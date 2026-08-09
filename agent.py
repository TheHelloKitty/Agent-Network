def post_to_x(text_content):
    if not client_id or not client_secret:
        return "Skipped (Missing X Secrets)"
    
    try:
        token_url = "https://api.x.com/2/oauth2/token"
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "client_type": "public"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(token_url, data=auth_data, headers=headers)
        
        if response.status_code != 200:
            return f"Auth Failed: {response.text}"
            
        token_json = response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            return "Auth Failed: No access token returned"
            
        tweet_url = "https://api.x.com/2/tweets"
        tweet_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"text": text_content}
        
        tweet_response = requests.post(tweet_url, headers=tweet_headers, json=payload)
        if tweet_response.status_code == 201:
            return "Successfully Posted Live!"
        else:
            return f"Post Failed: {tweet_response.status_code} - {tweet_response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"
