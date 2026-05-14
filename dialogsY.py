import requests
from config import YandexConfig


class YandexService:
    def __init__(self, logger):
        self.logger = logger
        self.config = YandexConfig()

    def upload_image(self, image_url):
        try:
            img_response = requests.get(image_url, timeout=5)
            if img_response.status_code != 200:
                self.logger.warning(f"Failed to download image: {image_url}")
                return None

            url = self.config.IMAGES_API_URL
            headers = {"Authorization": f"OAuth {self.config.OAUTH_TOKEN}"}
            files = {'file': ('image.jpg', img_response.content)}

            post_response = requests.post(url, headers=headers, files=files)

            if post_response.status_code == 201:
                image_id = post_response.json().get('image', {}).get('id')
                self.logger.info(f"Image uploaded successfully: {image_id}")
                return image_id

            self.logger.warning(f"Failed to upload image: {post_response.status_code}")
            return None

        except Exception as e:
            self.logger.error(f"Error uploading image: {e}")
            return None