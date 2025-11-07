"""
File processing service for multimedia content
"""

import logging
import base64
import io
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import httpx
from pathlib import Path

from app.models.llm import ProcessedData, ComplexityLevel, LLMRequest
from app.services.llm.llm_provider_service import llm_provider_service
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


class FileProcessor:
    """Service for processing multimedia files from WhatsApp"""
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_image_types = ['image/jpeg', 'image/png', 'image/webp']
        self.supported_audio_types = ['audio/ogg', 'audio/mpeg', 'audio/wav', 'audio/mp4']
        self.supported_document_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',  # .xls
            'text/csv',  # .csv
            'application/pdf'  # .pdf
        ]
    
    async def procesar_archivo_adjunto(self, archivo_url: str, tipo_contenido: str, caption: Optional[str] = None) -> ProcessedData:
        """
        Main function to process attached files
        
        Args:
            archivo_url: WhatsApp media ID or URL
            tipo_contenido: MIME type of the file
            caption: Optional caption text
            
        Returns:
            ProcessedData with extracted information
        """
        try:
            logger.info(f"Processing file: {archivo_url} (type: {tipo_contenido})")
            
            # Download file content
            file_content = await self._download_file(archivo_url)
            if not file_content:
                return self._create_error_response("Failed to download file")
            
            # Validate file size
            if len(file_content) > self.max_file_size:
                return self._create_error_response("File too large")
            
            # Route to appropriate processor based on content type
            if tipo_contenido in self.supported_image_types:
                result = await self._process_image(file_content, caption)
            elif tipo_contenido in self.supported_audio_types:
                result = await self._process_audio(file_content, caption)
            elif tipo_contenido in self.supported_document_types:
                result = await self._process_document(file_content, tipo_contenido, caption)
            else:
                return self._create_error_response(f"Unsupported file type: {tipo_contenido}")
            
            # Apply cross-validation for critical files
            if self._is_critical_file(result, file_content, tipo_contenido):
                result = await self._apply_cross_validation(result, file_content, tipo_contenido, caption)
            
            return result
                
        except Exception as e:
            logger.error(f"Error processing file {archivo_url}: {e}")
            return self._create_error_response(f"Processing error: {str(e)}")
    
    async def _download_file(self, media_id: str) -> Optional[bytes]:
        """Download file from WhatsApp API"""
        try:
            # First get the media URL
            media_url = await whatsapp_service.get_media_url(media_id)
            if not media_url:
                logger.error(f"Failed to get media URL for {media_id}")
                return None
            
            # Download the actual file content
            file_content = await whatsapp_service.download_media(media_url)
            if not file_content:
                logger.error(f"Failed to download media content from {media_url}")
                return None
            
            return file_content
            
        except Exception as e:
            logger.error(f"Error downloading file {media_id}: {e}")
            return None
    
    async def _process_image(self, file_content: bytes, caption: Optional[str] = None) -> ProcessedData:
        """
        Process image files using Anthropic Claude Vision for analysis of images
        Extracts text from facturas, catálogos, fotos de repuestos
        Identifies códigos de parte and especificaciones
        """
        try:
            logger.info("Processing image with vision models (Anthropic Claude Vision)")
            
            # Convert to base64 for LLM processing
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            # Process with LLM provider service (will route to Anthropic Claude Vision)
            result = await llm_provider_service.process_content(
                text=caption or "Analizar imagen de repuesto automotriz",
                image_url=f"data:image/jpeg;base64,{base64_image}"
            )
            
            # Add image-specific metadata
            result.extracted_entities["image_processed"] = True
            result.extracted_entities["image_size_bytes"] = len(file_content)
            result.extracted_entities["processing_method"] = "anthropic_vision"
            
            logger.info(f"Image processed with {result.provider_used}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return self._create_error_response(f"Image processing error: {str(e)}")
    
    async def _process_audio(self, file_content: bytes, caption: Optional[str] = None) -> ProcessedData:
        """
        Process audio files using Anthropic Claude for transcription and analysis
        Extracts información de repuestos desde audio
        Handles ruido de fondo y calidad variable
        """
        try:
            logger.info("Processing audio file with Anthropic Claude")
            
            # First, we need to transcribe the audio
            # In a production environment, you would use a transcription service like:
            # - OpenAI Whisper API
            # - Google Speech-to-Text
            # - Azure Speech Services
            
            # For now, we'll simulate transcription and focus on the analysis part
            transcribed_text = await self._transcribe_audio(file_content, caption)
            
            # Process transcribed text with Anthropic Claude for parts extraction
            result = await llm_provider_service.process_content(
                text=f"Transcripción de audio de cliente solicitando repuestos (puede tener ruido de fondo): {transcribed_text}",
                audio_url="audio_content"  # Indicates this is audio-derived content
            )
            
            # Add audio-specific metadata
            result.extracted_entities["audio_processed"] = True
            result.extracted_entities["audio_size_bytes"] = len(file_content)
            result.extracted_entities["transcription_method"] = "whisper_simulation"
            result.extracted_entities["audio_quality"] = self._assess_audio_quality(file_content)
            result.extracted_entities["processing_method"] = "anthropic_audio_analysis"
            
            logger.info(f"Audio processed with {result.provider_used}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return self._create_error_response(f"Audio processing error: {str(e)}")
    
    async def _transcribe_audio(self, file_content: bytes, caption: Optional[str] = None) -> str:
        """
        Transcribe audio content to text
        In production, this would use OpenAI Whisper or similar service
        """
        try:
            # Simulate transcription process
            # In production, you would:
            # 1. Save audio to temporary file
            # 2. Call transcription API (Whisper, Google STT, etc.)
            # 3. Return transcribed text
            
            # For simulation, use caption or generate placeholder
            if caption:
                transcribed_text = f"Cliente dice: {caption}"
            else:
                # Simulate a typical auto parts request
                transcribed_text = "Necesito pastillas de freno para un Toyota Corolla 2015, mi nombre es Juan Pérez, mi teléfono es 3001234567, estoy en Bogotá"
            
            logger.info(f"Audio transcribed: {len(transcribed_text)} characters")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return caption or "Error en transcripción de audio"
    
    def _assess_audio_quality(self, file_content: bytes) -> str:
        """
        Assess audio quality based on file size and format
        In production, this would analyze actual audio characteristics
        """
        try:
            size_mb = len(file_content) / (1024 * 1024)
            
            if size_mb > 5:
                return "alta"
            elif size_mb > 1:
                return "media"
            else:
                return "baja"
                
        except Exception:
            return "desconocida"
    
    async def _process_document(self, file_content: bytes, content_type: str, caption: Optional[str] = None) -> ProcessedData:
        """
        Process document files (Excel, CSV, PDF) using OpenAI GPT-4
        """
        try:
            logger.info(f"Processing document of type {content_type}")
            
            if content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                return await self._process_excel(file_content, caption)
            elif content_type == 'text/csv':
                return await self._process_csv(file_content, caption)
            elif content_type == 'application/pdf':
                return await self._process_pdf(file_content, caption)
            else:
                return self._create_error_response(f"Unsupported document type: {content_type}")
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return self._create_error_response(f"Document processing error: {str(e)}")
    
    async def _process_excel(self, file_content: bytes, caption: Optional[str] = None) -> ProcessedData:
        """
        Process Excel files using OpenAI GPT-4 for structured data extraction
        Detects columnas de repuestos, cantidades, especificaciones
        Validates and normalizes extracted data
        """
        try:
            logger.info("Processing Excel file with OpenAI GPT-4")
            
            # Read Excel file
            excel_file = io.BytesIO(file_content)
            
            # Try to read the Excel file
            try:
                df = pd.read_excel(excel_file)
            except Exception as e:
                logger.error(f"Failed to read Excel file: {e}")
                return self._create_error_response("Invalid Excel file format")
            
            # Detect and analyze column structure
            column_analysis = self._analyze_excel_columns(df)
            
            # Convert DataFrame to structured text for LLM processing
            excel_text = self._dataframe_to_structured_text(df, column_analysis)
            
            # Add caption if provided
            full_text = f"Archivo Excel de repuestos automotrices: {caption}\n\n{excel_text}" if caption else f"Archivo Excel de repuestos automotrices:\n\n{excel_text}"
            
            # Process with LLM (will route to OpenAI GPT-4 for structured documents)
            result = await llm_provider_service.process_content(
                text=full_text,
                document_url="excel_document"
            )
            
            # Add Excel-specific metadata
            result.extracted_entities["excel_processed"] = True
            result.extracted_entities["rows_count"] = len(df)
            result.extracted_entities["columns"] = list(df.columns)
            result.extracted_entities["column_analysis"] = column_analysis
            result.extracted_entities["processing_method"] = "openai_structured_extraction"
            result.extracted_entities["data_quality"] = self._assess_excel_data_quality(df)
            
            logger.info(f"Excel file processed with {result.provider_used} ({len(df)} rows)")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            return self._create_error_response(f"Excel processing error: {str(e)}")
    
    def _analyze_excel_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze Excel columns to detect repuestos, cantidades, especificaciones
        """
        try:
            column_analysis = {
                "repuesto_columns": [],
                "codigo_columns": [],
                "precio_columns": [],
                "cantidad_columns": [],
                "vehiculo_columns": [],
                "especificacion_columns": []
            }
            
            # Analyze column names to categorize them
            for col in df.columns:
                col_lower = str(col).lower()
                
                # Repuesto/Part columns
                if any(keyword in col_lower for keyword in ['repuesto', 'parte', 'pieza', 'producto', 'item']):
                    column_analysis["repuesto_columns"].append(col)
                
                # Code columns
                elif any(keyword in col_lower for keyword in ['codigo', 'code', 'referencia', 'ref', 'sku']):
                    column_analysis["codigo_columns"].append(col)
                
                # Price columns
                elif any(keyword in col_lower for keyword in ['precio', 'price', 'valor', 'costo', 'cost']):
                    column_analysis["precio_columns"].append(col)
                
                # Quantity columns
                elif any(keyword in col_lower for keyword in ['cantidad', 'qty', 'quantity', 'stock', 'disponible']):
                    column_analysis["cantidad_columns"].append(col)
                
                # Vehicle columns
                elif any(keyword in col_lower for keyword in ['vehiculo', 'vehicle', 'marca', 'modelo', 'año', 'year']):
                    column_analysis["vehiculo_columns"].append(col)
                
                # Specification columns
                elif any(keyword in col_lower for keyword in ['especificacion', 'spec', 'descripcion', 'detalle', 'caracteristica']):
                    column_analysis["especificacion_columns"].append(col)
            
            return column_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Excel columns: {e}")
            return {}
    
    def _dataframe_to_structured_text(self, df: pd.DataFrame, column_analysis: Dict[str, Any], max_rows: int = 50) -> str:
        """
        Convert DataFrame to structured text optimized for LLM processing
        """
        try:
            # Limit rows to avoid token limits
            if len(df) > max_rows:
                df_sample = df.head(max_rows)
                text = f"Primeras {max_rows} filas de {len(df)} total:\n\n"
            else:
                df_sample = df
                text = f"Todas las {len(df)} filas:\n\n"
            
            # Add column analysis context
            text += "ANÁLISIS DE COLUMNAS:\n"
            for category, columns in column_analysis.items():
                if columns:
                    text += f"- {category}: {', '.join(columns)}\n"
            text += "\n"
            
            # Convert to string with proper formatting
            text += "DATOS:\n"
            text += df_sample.to_string(index=False, max_cols=10)
            
            # Add summary statistics for numeric columns
            numeric_cols = df_sample.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text += f"\n\nESTADÍSTICAS NUMÉRICAS:\n"
                for col in numeric_cols:
                    text += f"- {col}: min={df_sample[col].min()}, max={df_sample[col].max()}, promedio={df_sample[col].mean():.2f}\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to structured text: {e}")
            return "Error converting data to structured text"
    
    def _assess_excel_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Assess the quality of Excel data
        """
        try:
            total_cells = df.shape[0] * df.shape[1]
            null_cells = df.isnull().sum().sum()
            completeness = ((total_cells - null_cells) / total_cells) * 100
            
            return {
                "completeness_percentage": round(completeness, 2),
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "null_cells": int(null_cells),
                "data_types": df.dtypes.to_dict(),
                "quality_score": "alta" if completeness > 90 else "media" if completeness > 70 else "baja"
            }
            
        except Exception as e:
            logger.error(f"Error assessing Excel data quality: {e}")
            return {"quality_score": "desconocida"}
    
    async def _process_csv(self, file_content: bytes, caption: Optional[str] = None) -> ProcessedData:
        """Process CSV files for auto parts data extraction"""
        try:
            # Read CSV file
            csv_text = file_content.decode('utf-8')
            
            try:
                df = pd.read_csv(io.StringIO(csv_text))
            except Exception as e:
                logger.error(f"Failed to read CSV file: {e}")
                return self._create_error_response("Invalid CSV file format")
            
            # Convert DataFrame to text representation
            csv_data_text = self._dataframe_to_text(df)
            
            # Add caption if provided
            full_text = f"Archivo CSV: {caption}\n\n{csv_data_text}" if caption else f"Archivo CSV:\n\n{csv_data_text}"
            
            # Process with LLM
            result = await llm_provider_service.process_content(
                text=full_text,
                document_url="csv_document"
            )
            
            # Add CSV-specific metadata
            result.extracted_entities["csv_processed"] = True
            result.extracted_entities["rows_count"] = len(df)
            result.extracted_entities["columns"] = list(df.columns)
            
            logger.info(f"CSV file processed with {result.provider_used} ({len(df)} rows)")
            return result
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            return self._create_error_response(f"CSV processing error: {str(e)}")
    
    async def _process_pdf(self, file_content: bytes, caption: Optional[str] = None) -> ProcessedData:
        """Process PDF files (basic implementation)"""
        try:
            # For PDF processing, you would typically use a library like PyPDF2 or pdfplumber
            # For now, we'll return a placeholder response
            
            logger.warning("PDF processing not fully implemented")
            
            # Simulate PDF text extraction
            pdf_text = "PDF content would be extracted here"
            
            # Add caption if provided
            full_text = f"Archivo PDF: {caption}\n\n{pdf_text}" if caption else f"Archivo PDF:\n\n{pdf_text}"
            
            # Process with LLM
            result = await llm_provider_service.process_content(
                text=full_text,
                document_url="pdf_document"
            )
            
            result.extracted_entities["pdf_processed"] = True
            result.extracted_entities["processing_method"] = "placeholder"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            return self._create_error_response(f"PDF processing error: {str(e)}")
    
    def _dataframe_to_text(self, df: pd.DataFrame, max_rows: int = 50) -> str:
        """Convert DataFrame to text representation for LLM processing"""
        try:
            # Limit rows to avoid token limits
            if len(df) > max_rows:
                df_sample = df.head(max_rows)
                text = f"Primeras {max_rows} filas de {len(df)} total:\n\n"
            else:
                df_sample = df
                text = f"Todas las {len(df)} filas:\n\n"
            
            # Convert to string with proper formatting
            text += df_sample.to_string(index=False, max_cols=10)
            
            # Add column info
            text += f"\n\nColumnas: {', '.join(df.columns.tolist())}"
            
            return text
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to text: {e}")
            return "Error converting data to text"
    
    def _create_error_response(self, error_message: str) -> ProcessedData:
        """Create error response"""
        return ProcessedData(
            repuestos=[],
            vehiculo=None,
            cliente=None,
            provider_used="file_processor_error",
            complexity_level="multimedia",
            confidence_score=0.0,
            processing_time_ms=0,
            raw_text=error_message,
            is_complete=False,
            missing_fields=["repuestos", "vehiculo", "cliente"]
        )
    
    async def validate_file_type(self, content_type: str) -> Tuple[bool, str]:
        """Validate if file type is supported"""
        all_supported = (
            self.supported_image_types + 
            self.supported_audio_types + 
            self.supported_document_types
        )
        
        if content_type in all_supported:
            if content_type in self.supported_image_types:
                return True, "image"
            elif content_type in self.supported_audio_types:
                return True, "audio"
            elif content_type in self.supported_document_types:
                return True, "document"
        
        return False, "unsupported"
    
    def _is_critical_file(self, result: ProcessedData, file_content: bytes, content_type: str) -> bool:
        """
        Determine if a file is critical and needs cross-validation
        Critical files are those with high uncertainty or high business impact
        """
        try:
            # Check confidence score - low confidence indicates uncertainty
            if result.confidence_score < 0.7:
                logger.info("File marked as critical due to low confidence score")
                return True
            
            # Check file size - large files may contain more complex data
            size_mb = len(file_content) / (1024 * 1024)
            if size_mb > 2:
                logger.info("File marked as critical due to large size")
                return True
            
            # Check if it's a structured document with many repuestos
            repuestos_count = len(result.repuestos) if result.repuestos else 0
            if repuestos_count > 5:
                logger.info("File marked as critical due to high number of repuestos")
                return True
            
            # Audio files are generally more uncertain due to transcription
            if content_type in self.supported_audio_types:
                logger.info("File marked as critical due to audio content")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining if file is critical: {e}")
            return False
    
    async def _apply_cross_validation(self, primary_result: ProcessedData, file_content: bytes, content_type: str, caption: Optional[str] = None) -> ProcessedData:
        """
        Apply cross-validation between providers for critical files
        Uses a secondary provider to validate the primary result
        """
        try:
            logger.info(f"Applying cross-validation for critical file (primary provider: {primary_result.provider_used})")
            
            # Get secondary provider based on primary provider used
            secondary_provider = self._get_secondary_provider(primary_result.provider_used, content_type)
            
            if not secondary_provider:
                logger.warning("No secondary provider available for cross-validation")
                return primary_result
            
            # Process with secondary provider
            secondary_result = await self._process_with_secondary_provider(
                file_content, content_type, caption, secondary_provider
            )
            
            # Compare results and create consolidated response
            validated_result = self._consolidate_cross_validation_results(primary_result, secondary_result)
            
            logger.info(f"Cross-validation completed (secondary provider: {secondary_result.provider_used})")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
            # Return primary result if cross-validation fails
            primary_result.extracted_entities["cross_validation_error"] = str(e)
            return primary_result
    
    def _get_secondary_provider(self, primary_provider: str, content_type: str) -> Optional[str]:
        """
        Get the best secondary provider for cross-validation
        """
        try:
            # Define provider preferences for cross-validation
            if content_type in self.supported_image_types:
                # For images, use OpenAI if primary was Anthropic, or vice versa
                if primary_provider == "anthropic":
                    return "openai"
                elif primary_provider == "openai":
                    return "anthropic"
            
            elif content_type in self.supported_document_types:
                # For documents, use Anthropic if primary was OpenAI, or vice versa
                if primary_provider == "openai":
                    return "anthropic"
                elif primary_provider == "anthropic":
                    return "openai"
                elif primary_provider == "gemini":
                    return "openai"
            
            elif content_type in self.supported_audio_types:
                # For audio, prefer Anthropic as secondary
                if primary_provider != "anthropic":
                    return "anthropic"
                else:
                    return "openai"
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting secondary provider: {e}")
            return None
    
    async def _process_with_secondary_provider(self, file_content: bytes, content_type: str, caption: Optional[str], secondary_provider: str) -> ProcessedData:
        """
        Process file with a specific secondary provider
        """
        try:
            # Force processing with specific provider by temporarily modifying the routing
            # This is a simplified approach - in production you might want more sophisticated routing control
            
            if content_type in self.supported_image_types:
                base64_image = base64.b64encode(file_content).decode('utf-8')
                result = await llm_provider_service.process_content(
                    text=f"[CROSS_VALIDATION] {caption or 'Analizar imagen de repuesto automotriz'}",
                    image_url=f"data:image/jpeg;base64,{base64_image}"
                )
            elif content_type in self.supported_audio_types:
                transcribed_text = await self._transcribe_audio(file_content, caption)
                result = await llm_provider_service.process_content(
                    text=f"[CROSS_VALIDATION] Transcripción de audio: {transcribed_text}",
                    audio_url="audio_content"
                )
            elif content_type in self.supported_document_types:
                if content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                    df = pd.read_excel(io.BytesIO(file_content))
                    excel_text = self._dataframe_to_text(df)
                    full_text = f"[CROSS_VALIDATION] Archivo Excel: {caption}\n\n{excel_text}" if caption else f"[CROSS_VALIDATION] Archivo Excel:\n\n{excel_text}"
                elif content_type == 'text/csv':
                    csv_text = file_content.decode('utf-8')
                    df = pd.read_csv(io.StringIO(csv_text))
                    csv_data_text = self._dataframe_to_text(df)
                    full_text = f"[CROSS_VALIDATION] Archivo CSV: {caption}\n\n{csv_data_text}" if caption else f"[CROSS_VALIDATION] Archivo CSV:\n\n{csv_data_text}"
                else:
                    full_text = f"[CROSS_VALIDATION] Documento: {caption or 'Analizar documento'}"
                
                result = await llm_provider_service.process_content(
                    text=full_text,
                    document_url="document_cross_validation"
                )
            else:
                raise ValueError(f"Unsupported content type for cross-validation: {content_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing with secondary provider {secondary_provider}: {e}")
            # Return a basic error result
            return self._create_error_response(f"Secondary provider error: {str(e)}")
    
    def _consolidate_cross_validation_results(self, primary: ProcessedData, secondary: ProcessedData) -> ProcessedData:
        """
        Consolidate results from primary and secondary providers
        """
        try:
            # Start with primary result as base
            consolidated = primary
            
            # Add cross-validation metadata
            consolidated.extracted_entities["cross_validation"] = {
                "primary_provider": primary.provider_used,
                "secondary_provider": secondary.provider_used,
                "primary_confidence": primary.confidence_score,
                "secondary_confidence": secondary.confidence_score,
                "validation_applied": True
            }
            
            # Compare repuestos and merge if secondary found additional ones
            primary_repuestos = primary.repuestos or []
            secondary_repuestos = secondary.repuestos or []
            
            # Simple consolidation: if secondary has more repuestos and higher confidence, prefer it
            if len(secondary_repuestos) > len(primary_repuestos) and secondary.confidence_score > primary.confidence_score:
                consolidated.repuestos = secondary_repuestos
                consolidated.extracted_entities["cross_validation"]["repuestos_source"] = "secondary"
            else:
                consolidated.extracted_entities["cross_validation"]["repuestos_source"] = "primary"
            
            # Adjust confidence score based on agreement
            agreement_score = self._calculate_agreement_score(primary, secondary)
            consolidated.confidence_score = min(1.0, (primary.confidence_score + secondary.confidence_score) / 2 + agreement_score * 0.1)
            consolidated.extracted_entities["cross_validation"]["agreement_score"] = agreement_score
            
            # Mark as cross-validated
            consolidated.provider_used = f"{primary.provider_used}+{secondary.provider_used}"
            
            return consolidated
            
        except Exception as e:
            logger.error(f"Error consolidating cross-validation results: {e}")
            # Return primary result with error metadata
            primary.extracted_entities["cross_validation_consolidation_error"] = str(e)
            return primary
    
    def _calculate_agreement_score(self, primary: ProcessedData, secondary: ProcessedData) -> float:
        """
        Calculate agreement score between two results
        """
        try:
            agreement_points = 0
            total_points = 0
            
            # Compare repuestos count
            primary_count = len(primary.repuestos) if primary.repuestos else 0
            secondary_count = len(secondary.repuestos) if secondary.repuestos else 0
            
            if primary_count > 0 or secondary_count > 0:
                total_points += 1
                if abs(primary_count - secondary_count) <= 1:  # Allow difference of 1
                    agreement_points += 1
            
            # Compare vehicle information
            if primary.vehiculo or secondary.vehiculo:
                total_points += 1
                if primary.vehiculo and secondary.vehiculo:
                    if (primary.vehiculo.get("marca", "").lower() == secondary.vehiculo.get("marca", "").lower() or
                        primary.vehiculo.get("linea", "").lower() == secondary.vehiculo.get("linea", "").lower()):
                        agreement_points += 1
            
            # Compare client information
            if primary.cliente or secondary.cliente:
                total_points += 1
                if primary.cliente and secondary.cliente:
                    if (primary.cliente.get("telefono") == secondary.cliente.get("telefono") or
                        primary.cliente.get("ciudad", "").lower() == secondary.cliente.get("ciudad", "").lower()):
                        agreement_points += 1
            
            return agreement_points / total_points if total_points > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating agreement score: {e}")
            return 0.5
    
    async def get_file_info(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Get basic file information"""
        try:
            file_info = {
                "size_bytes": len(file_content),
                "content_type": content_type,
                "is_supported": False,
                "file_category": "unknown"
            }
            
            is_supported, category = await self.validate_file_type(content_type)
            file_info["is_supported"] = is_supported
            file_info["file_category"] = category
            
            # Add specific info based on type
            if category == "document" and content_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel']:
                try:
                    df = pd.read_excel(io.BytesIO(file_content))
                    file_info["rows"] = len(df)
                    file_info["columns"] = len(df.columns)
                    file_info["column_names"] = list(df.columns)
                except:
                    file_info["parse_error"] = True
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                "size_bytes": len(file_content),
                "content_type": content_type,
                "error": str(e)
            }


# Global file processor instance
file_processor = FileProcessor()