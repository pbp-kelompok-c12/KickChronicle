from embed_video.backends import YoutubeBackend

class SecureYoutubeBackend(YoutubeBackend):
    """A YouTube backend that forces HTTPS embeds."""
    def get_embed_url(self):
        # Always use https, even if library tries http
        return f"https://www.youtube.com/embed/{self.code}"
