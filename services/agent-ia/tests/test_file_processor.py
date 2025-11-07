"""
Tests for File Processor Service
"""

import pytest
import io
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.file_processor import file_processor
from app.models.llm import ProcessedData

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_excel_content():
    """Create sample Excel content"""
    df = pd.DataFrame({
        'Repuesto': ['Pastillas de freno', 'Filtro de aceite', 'Bujías'],
        'Código': ['PF001', 'FA002', 'BJ003'],
        'Precio': [85000, 25000, 45000],
        'Vehículo': ['Toyota Corolla', 'Chevrolet Aveo', 'Nissan Sentra']
    })
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content"""
    csv_data = """Repuesto,Código,Precio,Vehículo
Pastillas de freno,PF001,85000,Toyota Corolla
Filtro de aceite,FA002,25000,Chevrolet Aveo
Bujías,BJ003,45000,Nissan Sentra"""
    return csv_data.encode('utf-8')


@pytest.fixture
def sample_processed_data():
    """Sample processed data response"""
    return ProcessedData(
        repuestos=[
            {
                "nombre": "pastillas de freno",
                "codigo": "PF001",
                "precio": "85000"
            }
        ],
        vehiculo={
            "marca": "Toyota",
            "linea": "Corolla"
        },
        cliente=None,
        provider_used="openai",
        complexity_level="structured",
        confidence_score=0.9,
        processing_time_ms=200,
        is_complete=True,
        missing_fields=[]
    )


class TestFileProcessor:
    """Test File Processor functionality"""
    
    async def test_validate_file_type_image(self):
        """Test image file type validation"""
        is_supported, category = await file_processor.validate_file_type('image/jpeg')
        assert is_supported is True
        assert category == "image"
        
        is_supported, category = await file_processor.validate_file_type('image/png')
        assert is_supported is True
        assert category == "image"
    
    async def test_validate_file_type_audio(self):
        """Test audio file type validation"""
        is_supported, category = await file_processor.validate_file_type('audio/ogg')
        assert is_supported is True
        assert category == "audio"
        
        is_supported, category = await file_processor.validate_file_type('audio/mpeg')
        assert is_supported is True
        assert category == "audio"
    
    async def test_validate_file_type_document(self):
        """Test document file type validation"""
        is_supported, category = await file_processor.validate_file_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        assert is_supported is True
        assert category == "document"
        
        is_supported, category = await file_processor.validate_file_type('text/csv')
        assert is_supported is True
        assert category == "document"
    
    async def test_validate_file_type_unsupported(self):
        """Test unsupported file type"""
        is_supported, category = await file_processor.validate_file_type('application/zip')
        assert is_supported is False
        assert category == "unsupported"
    
    @patch('app.services.file_processor.whatsapp_service.get_media_url')
    @patch('app.services.file_processor.whatsapp_service.download_media')
    async def test_download_file_success(self, mock_download, mock_get_url):
        """Test successful file download"""
        mock_get_url.return_value = "https://example.com/media.jpg"
        mock_download.return_value = b"fake_image_content"
        
        content = await file_processor._download_file("media123")
        
        assert content == b"fake_image_content"
        mock_get_url.assert_called_once_with("media123")
        mock_download.assert_called_once_with("https://example.com/media.jpg")
    
    @patch('app.services.file_processor.whatsapp_service.get_media_url')
    async def test_download_file_failure(self, mock_get_url):
        """Test file download failure"""
        mock_get_url.return_value = None
        
        content = await file_processor._download_file("media123")
        
        assert content is None
    
    def test_dataframe_to_text(self, sample_excel_content):
        """Test DataFrame to text conversion"""
        df = pd.read_excel(io.BytesIO(sample_excel_content))
        text = file_processor._dataframe_to_text(df)
        
        assert "Repuesto" in text
        assert "Pastillas de freno" in text
        assert "Columnas:" in text
        assert isinstance(text, str)
        assert len(text) > 0
    
    @patch('app.services.llm.llm_provider_service.llm_provider_service.process_content')
    async def test_process_excel(self, mock_process, sample_excel_content, sample_processed_data):
        """Test Excel file processing with OpenAI GPT-4"""
        # Enhance sample data for Excel processing
        enhanced_data = sample_processed_data
        enhanced_data.extracted_entities["excel_processed"] = True
        enhanced_data.extracted_entities["processing_method"] = "openai_structured_extraction"
        enhanced_data.extracted_entities["column_analysis"] = {
            "repuesto_columns": ["Repuesto"],
            "codigo_columns": ["Código"],
            "precio_columns": ["Precio"],
            "vehiculo_columns": ["Vehículo"]
        }
        enhanced_data.extracted_entities["data_quality"] = {"quality_score": "alta"}
        mock_process.return_value = enhanced_data
        
        result = await file_processor._process_excel(sample_excel_content, "Lista de repuestos")
        
        assert result.provider_used == "openai"
        assert result.extracted_entities.get("excel_processed") is True
        assert result.extracted_entities.get("rows_count") == 3
        assert "Repuesto" in result.extracted_entities.get("columns", [])
        assert result.extracted_entities.get("processing_method") == "openai_structured_extraction"
        assert result.extracted_entities.get("column_analysis") is not None
        assert result.extracted_entities.get("data_quality", {}).get("quality_score") == "alta"
        
        # Verify LLM was called with Excel data
        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert "Lista de repuestos" in call_args[1]["text"]
        assert "Pastillas de freno" in call_args[1]["text"]
        assert "ANÁLISIS DE COLUMNAS" in call_args[1]["text"]
    
    @patch('app.services.llm.llm_provider_service.llm_provider_service.process_content')
    async def test_process_csv(self, mock_process, sample_csv_content, sample_processed_data):
        """Test CSV file processing"""
        mock_process.return_value = sample_processed_data
        
        result = await file_processor._process_csv(sample_csv_content, "Catálogo CSV")
        
        assert result.provider_used == "openai"
        assert result.extracted_entities.get("csv_processed") is True
        assert result.extracted_entities.get("rows_count") == 3
        
        # Verify LLM was called with CSV data
        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert "Catálogo CSV" in call_args[1]["text"]
    
    @patch('app.services.llm.llm_provider_service.llm_provider_service.process_content')
    async def test_process_image(self, mock_process, sample_processed_data):
        """Test image processing with Anthropic Claude Vision"""
        # Enhance sample data for image processing
        enhanced_data = sample_processed_data
        enhanced_data.extracted_entities["image_processed"] = True
        enhanced_data.extracted_entities["processing_method"] = "anthropic_vision"
        mock_process.return_value = enhanced_data
        
        fake_image_content = b"fake_image_bytes"
        
        result = await file_processor._process_image(fake_image_content, "Foto del repuesto")
        
        assert result.provider_used == "openai"
        assert result.extracted_entities.get("image_processed") is True
        assert result.extracted_entities.get("processing_method") == "anthropic_vision"
        assert result.extracted_entities.get("image_size_bytes") == len(fake_image_content)
        
        # Verify LLM was called with image data
        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert "Foto del repuesto" in call_args[1]["text"]
        assert call_args[1]["image_url"].startswith("data:image/jpeg;base64,")  # Properly formatted data URL
    
    @patch('app.services.llm.llm_provider_service.llm_provider_service.process_content')
    async def test_process_audio(self, mock_process, sample_processed_data):
        """Test audio processing with Anthropic Claude"""
        # Enhance sample data for audio processing
        enhanced_data = sample_processed_data
        enhanced_data.extracted_entities["audio_processed"] = True
        enhanced_data.extracted_entities["transcription_method"] = "whisper_simulation"
        enhanced_data.extracted_entities["processing_method"] = "anthropic_audio_analysis"
        mock_process.return_value = enhanced_data
        
        fake_audio_content = b"fake_audio_bytes"
        
        result = await file_processor._process_audio(fake_audio_content, "Audio del cliente")
        
        assert result.provider_used == "openai"
        assert result.extracted_entities.get("audio_processed") is True
        assert result.extracted_entities.get("transcription_method") == "whisper_simulation"
        assert result.extracted_entities.get("processing_method") == "anthropic_audio_analysis"
        assert result.extracted_entities.get("audio_size_bytes") == len(fake_audio_content)
        assert result.extracted_entities.get("audio_quality") in ["alta", "media", "baja"]
        
        # Verify LLM was called with transcribed text
        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert "Audio del cliente" in call_args[1]["text"]
        assert call_args[1]["audio_url"] == "audio_content"
    
    @patch.object(file_processor, '_download_file')
    @patch.object(file_processor, '_process_excel')
    async def test_procesar_archivo_adjunto_excel(self, mock_process_excel, mock_download, sample_excel_content, sample_processed_data):
        """Test main file processing function with Excel"""
        mock_download.return_value = sample_excel_content
        mock_process_excel.return_value = sample_processed_data
        
        result = await file_processor.procesar_archivo_adjunto(
            "media123",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "Lista de repuestos"
        )
        
        assert result.provider_used == "openai"
        mock_download.assert_called_once_with("media123")
        mock_process_excel.assert_called_once_with(sample_excel_content, "Lista de repuestos")
    
    @patch.object(file_processor, '_download_file')
    async def test_procesar_archivo_adjunto_unsupported(self, mock_download):
        """Test processing unsupported file type"""
        mock_download.return_value = b"fake_content"
        
        result = await file_processor.procesar_archivo_adjunto(
            "media123",
            "application/zip",
            "Archivo ZIP"
        )
        
        assert result.provider_used == "file_processor_error"
        assert result.confidence_score == 0.0
        assert "Unsupported file type" in result.raw_text
    
    @patch.object(file_processor, '_download_file')
    async def test_procesar_archivo_adjunto_too_large(self, mock_download):
        """Test processing file that's too large"""
        # Create content larger than max_file_size
        large_content = b"x" * (file_processor.max_file_size + 1)
        mock_download.return_value = large_content
        
        result = await file_processor.procesar_archivo_adjunto(
            "media123",
            "image/jpeg",
            "Large image"
        )
        
        assert result.provider_used == "file_processor_error"
        assert "File too large" in result.raw_text
    
    @patch.object(file_processor, '_download_file')
    async def test_procesar_archivo_adjunto_download_failure(self, mock_download):
        """Test processing when file download fails"""
        mock_download.return_value = None
        
        result = await file_processor.procesar_archivo_adjunto(
            "media123",
            "image/jpeg",
            "Image"
        )
        
        assert result.provider_used == "file_processor_error"
        assert "Failed to download file" in result.raw_text
    
    async def test_get_file_info_excel(self, sample_excel_content):
        """Test getting file info for Excel"""
        file_info = await file_processor.get_file_info(
            sample_excel_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        assert file_info["is_supported"] is True
        assert file_info["file_category"] == "document"
        assert file_info["rows"] == 3
        assert file_info["columns"] == 4
        assert "Repuesto" in file_info["column_names"]
    
    async def test_get_file_info_unsupported(self):
        """Test getting file info for unsupported type"""
        fake_content = b"fake_content"
        
        file_info = await file_processor.get_file_info(
            fake_content,
            "application/zip"
        )
        
        assert file_info["is_supported"] is False
        assert file_info["file_category"] == "unsupported"
        assert file_info["size_bytes"] == len(fake_content)
    
    def test_create_error_response(self):
        """Test error response creation"""
        error_response = file_processor._create_error_response("Test error")
        
        assert error_response.provider_used == "file_processor_error"
        assert error_response.confidence_score == 0.0
        assert error_response.raw_text == "Test error"
        assert error_response.is_complete is False
    
    def test_is_critical_file_low_confidence(self, sample_processed_data):
        """Test critical file detection based on low confidence"""
        sample_processed_data.confidence_score = 0.5  # Low confidence
        fake_content = b"fake_content"
        
        is_critical = file_processor._is_critical_file(sample_processed_data, fake_content, "image/jpeg")
        
        assert is_critical is True
    
    def test_is_critical_file_large_size(self, sample_processed_data):
        """Test critical file detection based on large file size"""
        sample_processed_data.confidence_score = 0.9  # High confidence
        large_content = b"x" * (3 * 1024 * 1024)  # 3MB file
        
        is_critical = file_processor._is_critical_file(sample_processed_data, large_content, "image/jpeg")
        
        assert is_critical is True
    
    def test_is_critical_file_many_repuestos(self, sample_processed_data):
        """Test critical file detection based on many repuestos"""
        sample_processed_data.confidence_score = 0.9  # High confidence
        sample_processed_data.repuestos = [{"nombre": f"repuesto_{i}"} for i in range(10)]  # Many repuestos
        fake_content = b"fake_content"
        
        is_critical = file_processor._is_critical_file(sample_processed_data, fake_content, "image/jpeg")
        
        assert is_critical is True
    
    def test_is_critical_file_audio_content(self, sample_processed_data):
        """Test critical file detection for audio content"""
        sample_processed_data.confidence_score = 0.9  # High confidence
        fake_content = b"fake_audio"
        
        is_critical = file_processor._is_critical_file(sample_processed_data, fake_content, "audio/ogg")
        
        assert is_critical is True
    
    def test_is_not_critical_file(self, sample_processed_data):
        """Test non-critical file detection"""
        sample_processed_data.confidence_score = 0.9  # High confidence
        sample_processed_data.repuestos = [{"nombre": "repuesto_1"}]  # Few repuestos
        fake_content = b"fake_content"  # Small file
        
        is_critical = file_processor._is_critical_file(sample_processed_data, fake_content, "image/jpeg")
        
        assert is_critical is False
    
    def test_get_secondary_provider_image(self):
        """Test secondary provider selection for images"""
        # Anthropic primary -> OpenAI secondary
        secondary = file_processor._get_secondary_provider("anthropic", "image/jpeg")
        assert secondary == "openai"
        
        # OpenAI primary -> Anthropic secondary
        secondary = file_processor._get_secondary_provider("openai", "image/jpeg")
        assert secondary == "anthropic"
    
    def test_get_secondary_provider_document(self):
        """Test secondary provider selection for documents"""
        # OpenAI primary -> Anthropic secondary
        secondary = file_processor._get_secondary_provider("openai", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert secondary == "anthropic"
        
        # Gemini primary -> OpenAI secondary
        secondary = file_processor._get_secondary_provider("gemini", "text/csv")
        assert secondary == "openai"
    
    def test_get_secondary_provider_audio(self):
        """Test secondary provider selection for audio"""
        # Non-Anthropic primary -> Anthropic secondary
        secondary = file_processor._get_secondary_provider("openai", "audio/ogg")
        assert secondary == "anthropic"
        
        # Anthropic primary -> OpenAI secondary
        secondary = file_processor._get_secondary_provider("anthropic", "audio/ogg")
        assert secondary == "openai"
    
    def test_calculate_agreement_score_high_agreement(self, sample_processed_data):
        """Test agreement score calculation with high agreement"""
        primary = sample_processed_data
        
        # Create a similar secondary result
        secondary = ProcessedData(
            repuestos=[{"nombre": "pastillas"}],
            vehiculo={"marca": "Toyota", "linea": "Corolla"},
            cliente=None,
            provider_used="anthropic",
            complexity_level="structured",
            confidence_score=0.85,
            processing_time_ms=300,
            is_complete=True,
            missing_fields=[]
        )
        
        # Set same data for primary
        primary.repuestos = [{"nombre": "pastillas"}]
        primary.vehiculo = {"marca": "Toyota", "linea": "Corolla"}
        
        agreement = file_processor._calculate_agreement_score(primary, secondary)
        
        assert agreement > 0.5  # Should have good agreement
    
    def test_calculate_agreement_score_low_agreement(self, sample_processed_data):
        """Test agreement score calculation with low agreement"""
        primary = sample_processed_data
        secondary = ProcessedData(
            repuestos=[{"nombre": "filtro"}, {"nombre": "aceite"}],  # Different repuestos
            vehiculo={"marca": "Chevrolet", "linea": "Aveo"},  # Different vehicle
            cliente=None,
            provider_used="anthropic",
            complexity_level="structured",
            confidence_score=0.8,
            processing_time_ms=300,
            is_complete=True,
            missing_fields=[]
        )
        
        agreement = file_processor._calculate_agreement_score(primary, secondary)
        
        assert agreement < 0.8  # Should have lower agreement
    
    @patch.object(file_processor, '_process_with_secondary_provider')
    @patch.object(file_processor, '_get_secondary_provider')
    async def test_apply_cross_validation(self, mock_get_secondary, mock_process_secondary, sample_processed_data):
        """Test cross-validation application"""
        # Setup mocks
        mock_get_secondary.return_value = "anthropic"
        
        secondary_result = ProcessedData(
            repuestos=[{"nombre": "pastillas de freno"}],
            vehiculo={"marca": "Toyota", "linea": "Corolla"},
            cliente=None,
            provider_used="anthropic",
            complexity_level="multimedia",
            confidence_score=0.85,
            processing_time_ms=400,
            is_complete=True,
            missing_fields=[]
        )
        mock_process_secondary.return_value = secondary_result
        
        fake_content = b"fake_content"
        
        result = await file_processor._apply_cross_validation(
            sample_processed_data, fake_content, "image/jpeg", "Test caption"
        )
        
        # Verify cross-validation metadata was added
        assert result.extracted_entities.get("cross_validation") is not None
        assert result.extracted_entities["cross_validation"]["primary_provider"] == "openai"
        assert result.extracted_entities["cross_validation"]["secondary_provider"] == "anthropic"
        assert result.extracted_entities["cross_validation"]["validation_applied"] is True
        assert "agreement_score" in result.extracted_entities["cross_validation"]
        
        # Verify provider was combined
        assert "+" in result.provider_used
        
        mock_get_secondary.assert_called_once_with("openai", "image/jpeg")
        mock_process_secondary.assert_called_once()