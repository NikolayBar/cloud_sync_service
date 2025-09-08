from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseCloudProvider(ABC):
    """Абстрактный базовый класс для всех облачных провайдеров."""

    def __init__(self, access_token: str, cloud_folder: str):
        self.access_token = access_token
        self.cloud_folder = cloud_folder

    @abstractmethod
    def load(self, local_path: str, cloud_filename: str) -> bool:
        """Загружает новый файл в облачное хранилище."""
        pass

    @abstractmethod
    def reload(self, local_path: str, cloud_filename: str) -> bool:
        """Перезаписывает существующий файл в облачном хранилище."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Удаляет файл из облачного хранилища."""
        pass

    @abstractmethod
    def get_info(self) -> Optional[Dict]:
        """Получает информацию о файлах в облачном хранилище."""
        pass