import os
import time
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from cloud_providers import LocalMockProvider, YandexDiskProvider


def load_config():
    """Загружает конфигурацию из файла .env и выполняет валидацию."""
    load_dotenv()

    config = {}
    config["local_folder"] = os.getenv("LOCAL_FOLDER_PATH")
    config["cloud_folder"] = os.getenv("CLOUD_FOLDER_NAME")
    config["access_token"] = os.getenv("ACCESS_TOKEN")
    config["sync_interval"] = int(os.getenv("SYNC_INTERVAL", 300))
    config["log_path"] = os.getenv("LOG_PATH", "sync_log.log")
    config["cloud_provider"] = os.getenv("CLOUD_PROVIDER", "yandex")

    if not config["local_folder"]:
        raise ValueError("Parameter 'LOCAL_FOLDER_PATH' is not set in .env file.")
    if not config["cloud_folder"]:
        raise ValueError("Parameter 'CLOUD_FOLDER_NAME' is not set in .env file.")
    if not config["access_token"]:
        raise ValueError("Parameter 'ACCESS_TOKEN' is not set in .env file.")

    if not os.path.isdir(config["local_folder"]):
        raise FileNotFoundError(f"Local folder '{config['local_folder']}' does not exist.")

    return config


def setup_logging(log_path: str):
    """Настраивает логирование в файл."""
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger.add(log_path, rotation="10 MB", level="INFO", enqueue=True)
    logger.info("Logging setup complete.")


def get_cloud_provider(config: dict):
    """Фабричный метод для создания экземпляра провайдера."""
    provider_type = config["cloud_provider"].lower()

    if provider_type == "yandex":
        return YandexDiskProvider(config["access_token"], config["cloud_folder"])
    elif provider_type == "local_mock":
        return LocalMockProvider(config["access_token"], config["cloud_folder"])
    else:
        raise ValueError(f"Unknown cloud provider: {provider_type}. Available: 'yandex', 'local_mock'")


def get_local_state(local_folder_path: str):
    """Сканирует локальную папку и возвращает состояние файлов."""
    local_state = {}
    try:
        for item in Path(local_folder_path).iterdir():
            if item.is_file():
                local_state[item.name] = item.stat().st_mtime
    except OSError as e:
        logger.error(f"Error reading local directory {local_folder_path}: {e}")
    return local_state


def get_cloud_state(cloud_provider):
    """Получает список файлов в облачной папке."""
    cloud_info = cloud_provider.get_info()
    cloud_state = {}
    if cloud_info and "_embedded" in cloud_info and "items" in cloud_info["_embedded"]:
        for item in cloud_info["_embedded"]["items"]:
            if item["type"] == "file":
                cloud_state[item["name"]] = True
    return cloud_state


def sync(local_folder: str, cloud_provider):
    """Выполняет одну итерацию синхронизации."""
    logger.info("Starting synchronization cycle.")

    try:
        local_files = get_local_state(local_folder)
        cloud_files = get_cloud_state(cloud_provider)

        # Удаляем из облака файлы, которых нет локально
        for filename in list(cloud_files.keys()):
            if filename not in local_files:
                logger.info(f"File {filename} missing locally. Deleting from cloud.")
                success = cloud_provider.delete(filename)
                if success:
                    logger.info(f"Successfully deleted {filename} from cloud.")

        # Синхронизируем файлы, которые есть локально
        for filename, local_mtime in local_files.items():
            local_file_path = os.path.join(local_folder, filename)

            if filename in cloud_files:
                logger.info(f"File {filename} exists in cloud. Checking for changes...")
                success = cloud_provider.reload(local_file_path, filename)
                if success:
                    logger.info(f"Successfully updated {filename} in cloud.")
            else:
                logger.info(f"New file {filename} found. Uploading to cloud.")
                success = cloud_provider.load(local_file_path, filename)
                if success:
                    logger.info(f"Successfully uploaded {filename} to cloud.")

    except Exception as e:
        logger.error(f"Error during synchronization: {e}")

    logger.info("Synchronization cycle finished.")


def main():
    """Главная функция приложения."""
    try:
        config = load_config()
        setup_logging(config["log_path"])
        logger.info(f"Service started. Syncing folder: {config['local_folder']}")

        cloud_provider = get_cloud_provider(config)

        # Первая синхронизация при запуске
        sync(config["local_folder"], cloud_provider)

        # Основной цикл работы
        while True:
            time.sleep(config["sync_interval"])
            sync(config["local_folder"], cloud_provider)
            logger.info(f"Next sync in {config['sync_interval']} seconds.")

    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and try again.")
    except KeyboardInterrupt:
        logger.info("Service stopped by user.")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        print(f"A critical error occurred. See log file for details.")


if __name__ == "__main__":
    main()