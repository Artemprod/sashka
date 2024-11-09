from io import BytesIO
from typing import Union
from zipfile import ZipFile

from starlette.responses import StreamingResponse


from src.services.analitcs.models.analitic import AnalyticDataBufferDTO, AnalyticFileDTO


class ZIPFileHandler:
    def __init__(self,
                 data: Union[AnalyticDataBufferDTO, AnalyticFileDTO],
                 file_extension: str):
        self.data = data
        self.file_extension = file_extension

    def create_response(self) -> StreamingResponse:
        zip_file = self._create_zip_file()
        return StreamingResponse(
            zip_file,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=research_data.zip"}
        )

    def _create_zip_file(self) -> BytesIO:
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
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
        zip_buffer.seek(0)
        return zip_buffer
