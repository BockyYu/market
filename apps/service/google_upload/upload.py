# coding: utf8
import logging
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from apps.config.config import Configs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleDriveUploader:
    def __init__(self):
        cnf_upload = Configs.get("Upload")
        self.upload_folder = cnf_upload.get("UploadFolder")
        self.scopes = cnf_upload.get("Scopes")
        # 修正 key.json 的路徑
        self.service_account_file = Path(__file__).parent / 'key.json'
        self._service = None

    @property
    def service(self):
        """延遲加載 Google Drive service"""
        if self._service is None:
            try:
                if not self.service_account_file.exists():
                    raise FileNotFoundError(f"Service account key file not found: {self.service_account_file}")

                creds = service_account.Credentials.from_service_account_file(
                    str(self.service_account_file),
                    scopes=self.scopes
                )
                self._service = build('drive', 'v3', credentials=creds)
            except Exception as e:
                logger.error(f"Failed to initialize Google Drive service: {e}")
                raise

        return self._service

    def check_and_delete_existing_file(self, filename: str) -> None:
        """
        檢查並刪除已存在的檔案

        Args:
            filename: 檔案名稱
        """
        try:
            # 查找指定資料夾中的同名檔案
            query = f"name = '{filename}' and '{self.upload_folder}' in parents and trashed = false"
            logger.info(f"Searching for existing file with query: {query}")

            results = self.service.files().list(
                q=query,
                fields="files(id, name, parents)",
                spaces='drive'
            ).execute()

            existing_files = results.get('files', [])
            logger.info(f"Found {len(existing_files)} existing files with name: {filename}")

            # 如果找到檔案，列出詳細資訊並刪除
            for file in existing_files:
                logger.info(f"Found file: {file['name']} (ID: {file['id']}, Parents: {file.get('parents', [])})")
                try:
                    self.service.files().delete(fileId=file['id']).execute()
                    logger.info(f"Successfully deleted file: {file['name']} (ID: {file['id']})")
                except Exception as delete_error:
                    logger.error(f"Failed to delete file {file['id']}: {delete_error}")
                    raise

        except Exception as e:
            logger.error(f"Error handling existing file: {e}")
            raise

    def upload_file(self, file_path: str) -> Optional[Dict]:
        """
        上傳檔案到 Google Drive，確保資料夾中只保留最新版本

        Args:
            file_path: 要上傳的檔案路徑

        Returns:
            Dict: 上傳成功時返回檔案資訊
            None: 上傳失敗時返回 None

        Raises:
            FileNotFoundError: 當檔案不存在時
            HttpError: 當 Google Drive API 呼叫失敗時
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            logger.info(f"Processing file: {file_path.name}")
            logger.info(f"Upload folder ID: {self.upload_folder}")

            # 先檢查並刪除已存在的同名檔案
            self.check_and_delete_existing_file(file_path.name)

            # 準備上傳新檔案
            logger.info(f"Starting upload for new file: {file_path.name}")

            file_metadata = {
                'name': file_path.name,
                'parents': [self.upload_folder]
            }

            logger.info(f"File metadata: {file_metadata}")

            # 建立檔案物件並設定 resumable=True 支援大檔案斷點續傳
            media = MediaFileUpload(
                str(file_path),
                resumable=True,
                chunksize=256 * 1024  # 256KB chunks
            )

            # 執行上傳
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType,size,modifiedTime,parents'  # 指定要返回的檔案資訊
            ).execute()

            logger.info(f"Successfully uploaded new file. Details: {file}")
            return file

        except HttpError as e:
            logger.error(f"HTTP error occurred while uploading {file_path.name}: {e.content}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while uploading {file_path.name}: {e}")
            raise


def do_upload():
    """主要上傳函數"""
    try:
        uploader = GoogleDriveUploader()

        current_time = datetime.now()

        current_file = Path(__file__).resolve()  # 取得當前檔案的絕對路徑
        apps_dir = current_file.parent.parent.parent  # 往上三層到 market 目錄
        filename = apps_dir / f"market_data_{current_time.strftime('%Y%m%d')}.xlsx"

        logger.info(f"Attempting to upload file from: {filename}")

        # 執行上傳
        result = uploader.upload_file(str(filename))
        return result

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise


if __name__ == "__main__":
    do_upload()