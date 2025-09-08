import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from .base import BaseCloudProvider


class LocalMockProvider(BaseCloudProvider):
    """
    Локальная заглушка, имитирующая облачное хранилище.
    Синхронизирует файлы между двумя локальными папками.
    """

    def __init__(self, access_token: str, cloud_folder: str):
        super().__init__(access_token, cloud_folder)
        self.mock_cloud_path = Path(access_token) / cloud_folder
        self.mock_cloud_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local mock provider initialized. Cloud folder: {self.mock_cloud_path}")

    def load(self, local_path: str, cloud_filename: str) -> bool:
        """Копирует файл в папку-заглушку."""
        try:
            destination = self.mock_cloud_path / cloud_filename
            shutil.copy2(local_path, destination)
            logger.info(f"MOCK: Copied {cloud_filename} to mock cloud")
            return True
        except Exception as e:
            logger.error(f"MOCK: Error copying {cloud_filename}: {e}")
            return False

    def reload(self, local_path: str, cloud_filename: str) -> bool:
        """Перезаписывает файл в папке-заглушке."""
        return self.load(local_path, cloud_filename)

    def delete(self, filename: str) -> bool:
        """Удаляет файл из папки-заглушки."""
        try:
            file_to_delete = self.mock_cloud_path / filename
            if file_to_delete.exists():
                file_to_delete.unlink()
                logger.info(f"MOCK: Deleted {filename} from mock cloud")
            return True
        except Exception as e:
            logger.error(f"MOCK: Error deleting {filename}: {e}")
            return False

    def get_info(self) -> Optional[Dict]:
        """Возвращает информацию о файлах в папке-заглушке."""
        try:
            files = {}
            for item in self.mock_cloud_path.iterdir():
                if item.is_file():
                    files[item.name] = {
                        "path": str(item),
                        "size": item.stat().st_size
                    }
            return {"_embedded": {"items": [{"name": k, "type": "file", **v} for k, v in files.items()]}}
        except Exception as e:
            logger.error(f"MOCK: Error reading mock cloud info: {e}")
            return None