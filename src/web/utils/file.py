import os
from io import BytesIO
from typing import Union
from zipfile import ZipFile

from tempfile import NamedTemporaryFile
from starlette.responses import StreamingResponse

from src.services.analitcs.models.analitic import AnalyticDataBufferDTO
from src.services.analitcs.models.analitic import AnalyticFileDTO
from src.services.cloud_storage.s3.clietn import S3Client


# class ZIPFileHandler:
#     def __init__(self,
#                  storage,
#                  data: Union[AnalyticDataBufferDTO, AnalyticFileDTO],
#                  file_extension: str):
#         self.data = data
#         self.file_extension = file_extension
#         self.storage = storage
#
#     def create_response(self) -> StreamingResponse:
#         zip_file = self._create_zip_file()
#         return StreamingResponse(
#             zip_file,
#             media_type="application/zip",
#             headers={"Content-Disposition": "attachment; filename=research_data.zip"}
#         )
#
#     def _create_zip_file(self) -> BytesIO:
#         zip_buffer = BytesIO()
#         with ZipFile(zip_buffer, "w") as zip_file:
#             if isinstance(self.data, AnalyticDataBufferDTO):
#                 for i, dialog in enumerate(self.data.dialogs):
#                     zip_file.writestr(f"dialog_{i + 1}.{self.file_extension}", dialog.getvalue())
#                 zip_file.writestr(f"metrics.{self.file_extension}", self.data.metric.getvalue())
#             elif isinstance(self.data, AnalyticFileDTO):
#                 for i, dialog_path in enumerate(self.data.dialogs):
#                     with open(dialog_path, "rb") as file:
#                         zip_file.writestr(f"dialog_{i + 1}.{self.file_extension}", file.read())
#                 with open(self.data.metric, "rb") as metric_file:
#                     zip_file.writestr(f"metrics.{self.file_extension}", metric_file.read())
#         zip_buffer.seek(0)
#         return zip_buffer

class ZIPFileHandler:
    def __init__(self, storage: S3Client, data: Union[AnalyticDataBufferDTO, AnalyticFileDTO], file_extension: str):
        self.data = data
        self.file_extension = file_extension
        self.storage = storage

    async def save_and_upload_file(self) -> str:
        temp_zip = None
        try:
            temp_zip = NamedTemporaryFile(delete=False, suffix=".zip", dir="static")
            file_path = temp_zip.name
            self._create_zip_file(file_path)
            # Убедимся, что файл закрыт, прежде чем совершать какие-либо действия
            temp_zip.close()

            # Загрузка файла в облачное хранилище
            object_name = await self.storage.upload_file(file_path)

            return object_name
        finally:
            # Удаляем временный файл после загрузки
            if temp_zip is not None:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Could not remove the file: {e}")

    def _create_zip_file(self, file_path: str) -> None:
        with ZipFile(file_path, "w") as zip_file:
            if isinstance(self.data, AnalyticDataBufferDTO):
                for i, dialog in enumerate(self.data.dialogs):
                    zip_file.writestr(f"dialog_{i + 1}.{self.file_extension}", dialog.getvalue())
                zip_file.writestr(f"metrics.{self.file_extension}", self.data.metric.getvalue())
            elif isinstance(self.data, AnalyticFileDTO):
                for i, dialog_path in enumerate(self.data.dialogs):
                    with open(dialog_path, "rb") as file:
                        zip_file.writestr(f"dialog_{i + 1}.{self.file_extension}", file.read())
                with open(self.data.metric, "rb") as metric_file:
                    zip_file.writestr(f"metrics.{self.file_extension}", metric_file.read())