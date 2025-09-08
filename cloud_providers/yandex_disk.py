import requests
from typing import Dict, Optional
from loguru import logger
from .base import BaseCloudProvider


class YandexDiskProvider(BaseCloudProvider):
    """Реализация для Yandex Disk API."""

    def __init__(self, access_token: str, cloud_folder: str):
        super().__init__(access_token, cloud_folder)
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {
            "Authorization": f"OAuth {self.access_token}",
            "Accept": "application/json"
        }

    def _check_response(self, response: requests.Response) -> bool:
        """Проверяет ответ API на ошибки."""
        if response.status_code not in (200, 201, 202, 204):
            logger.error(f"Yandex Disk API error: {response.status_code} - {response.text}")
            return False
        return True

    def load(self, local_path: str, cloud_filename: str) -> bool:
        upload_url = f"{self.base_url}/upload"
        params = {
            "path": f"{self.cloud_folder}/{cloud_filename}",
            "overwrite": "false"
        }

        try:
            response = requests.get(upload_url, headers=self.headers, params=params)
            if not self._check_response(response):
                return False

            href = response.json().get("href")
            with open(local_path, "rb") as f:
                response_upload = requests.put(href, files={"file": f})
            return self._check_response(response_upload)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during upload of {cloud_filename}: {e}")
            return False
        except OSError as e:
            logger.error(f"Error reading local file {local_path}: {e}")
            return False

    def reload(self, local_path: str, cloud_filename: str) -> bool:
        upload_url = f"{self.base_url}/upload"
        params = {
            "path": f"{self.cloud_folder}/{cloud_filename}",
            "overwrite": "true"
        }

        try:
            response = requests.get(upload_url, headers=self.headers, params=params)
            if not self._check_response(response):
                return False

            href = response.json().get("href")
            with open(local_path, "rb") as f:
                response_upload = requests.put(href, files={"file": f})
            return self._check_response(response_upload)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during reload of {cloud_filename}: {e}")
            return False
        except OSError as e:
            logger.error(f"Error reading local file {local_path}: {e}")
            return False

    def delete(self, filename: str) -> bool:
        delete_url = f"{self.base_url}"
        params = {"path": f"{self.cloud_folder}/{filename}", "permanently": "true"}

        try:
            response = requests.delete(delete_url, headers=self.headers, params=params)
            if response.status_code == 404:
                logger.info(f"File {filename} not found in cloud. Skipping delete.")
                return True
            return self._check_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during deletion of {filename}: {e}")
            return False

    def get_info(self) -> Optional[Dict]:
        params = {"path": self.cloud_folder, "limit": 1000}

        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            if not self._check_response(response):
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching cloud info: {e}")
            return None