from src.services.analitcs.models.metrics import DialogMetrics
import csv
import io
from datetime import datetime
from pathlib import Path
from typing import List, Union

import pandas as pd


class CsvExporter:
    @staticmethod
    def export_to_csv(data: List['DialogMetrics'], filepath: Union[str, Path], encoding: str = 'utf-8') -> None:
        """Экспорт списка объектов DialogMetrics в CSV файл."""
        if not data:
            raise ValueError("Список данных для экспорта не может быть пустым")

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with filepath.open(mode='w', newline='', encoding=encoding) as csv_file:
                fieldnames = list(data[0].model_dump().keys())
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)

                writer.writeheader()
                for item in data:
                    row_dict = item.model_dump()
                    if isinstance(row_dict['timestamp'], datetime):
                        row_dict['timestamp'] = row_dict['timestamp'].isoformat()
                    writer.writerow(row_dict)

        except OSError as e:
            raise OSError(f"Ошибка при записи CSV файла: {e}")

    @staticmethod
    def export_to_csv_buffer(data: List['DialogMetrics'], encoding: str = 'utf-8') -> io.BytesIO:
        """Экспорт списка объектов DialogMetrics в CSV буфер."""
        if not data:
            raise ValueError("Список данных для экспорта не может быть пустым")

        string_buffer = io.StringIO()

        try:
            fieldnames = list(data[0].model_dump().keys())
            writer = csv.DictWriter(string_buffer, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)

            writer.writeheader()
            for item in data:
                row_dict = item.model_dump()
                if isinstance(row_dict['timestamp'], datetime):
                    row_dict['timestamp'] = row_dict['timestamp'].isoformat()
                writer.writerow(row_dict)

            byte_buffer = io.BytesIO()
            byte_buffer.write(string_buffer.getvalue().encode(encoding))
            byte_buffer.seek(0)

            return byte_buffer

        except Exception as e:
            raise RuntimeError(f"Ошибка при записи CSV в буфер: {e}")


class ExcelExporter:
    @staticmethod
    def export_to_excel(data: List['DialogMetrics'], filepath: Union[str, Path]) -> None:
        """Экспорт списка объектов DialogMetrics в Excel файл."""
        if not data:
            raise ValueError("Список данных для экспорта не может быть пустым")

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            df = pd.DataFrame([item.model_dump() for item in data])
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)

        except OSError as e:
            raise OSError(f"Ошибка при записи Excel файла: {e}")

    @staticmethod
    def export_to_excel_buffer(data: List['DialogMetrics']) -> io.BytesIO:
        """Экспорт списка объектов DialogMetrics в Excel буфер."""
        if not data:
            raise ValueError("Список данных для экспорта не может быть пустым")

        byte_buffer = io.BytesIO()

        try:
            df = pd.DataFrame([item.model_dump() for item in data])
            with pd.ExcelWriter(byte_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)

            byte_buffer.seek(0)

            return byte_buffer

        except Exception as e:
            raise RuntimeError(f"Ошибка при записи Excel в буфер: {e}")


if __name__ == "__main__":
    metrics_list = [
        DialogMetrics(total_dialogs=100, answered_first=60, conversion_rate=60.0),
        DialogMetrics(total_dialogs=150, answered_first=90, conversion_rate=60.0),
    ]
    print(ExcelExporter.export_to_excel_buffer(metrics_list))
