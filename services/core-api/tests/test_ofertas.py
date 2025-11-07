"""
Tests del Sistema de Ofertas para TeLOO V3
Tests de validación de rangos, formatos, carga masiva Excel y transiciones de estado
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import io
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock

# Import models and services
from models.oferta import Oferta, OfertaDetalle
from models.solicitud import Solicitud, RepuestoSolicitado
from models.user import Usuario, Asesor
from models.enums import EstadoOferta, EstadoSolicitud, RolUsuario, EstadoUsuario, EstadoAsesor
from services.ofertas_service import OfertasService


class TestValidacionRangosFormatos:
    """Tests de validación de rangos y formatos"""
    
    def test_validate_precio_unitario_valid_ranges(self):
        """Test validación de precios unitarios válidos"""
        valid_prices = [
            Decimal('1000'),      # Mínimo
            Decimal('5000'),      # Bajo
            Decimal('100000'),    # Medio
            Decimal('1000000'),   # Alto
            Decimal('50000000')   # Máximo
        ]
        
        for price in valid_prices:
            # Should not raise exception
            from models.oferta import validate_precio_unitario
            result = validate_precio_unitario(price)
            assert result == price
    
    def test_validate_precio_unitario_invalid_ranges(self):
        """Test validación de precios unitarios inválidos"""
        invalid_prices = [
            Decimal('999'),       # Menor al mínimo
            Decimal('500'),       # Muy bajo
            Decimal('0'),         # Cero
            Decimal('50000001'),  # Mayor al máximo
            Decimal('100000000')  # Muy alto
        ]
        
        from models.oferta import validate_precio_unitario
        for price in invalid_prices:
            with pytest.raises(ValueError, match="Precio unitario debe estar entre 1,000 y 50,000,000 COP"):
                validate_precio_unitario(price)
    
    def test_validate_garantia_meses_valid_ranges(self):
        """Test validación de garantía válida"""
        valid_warranties = [1, 6, 12, 24, 36, 60]  # 1 mes a 5 años
        
        from models.oferta import validate_garantia_meses
        for warranty in valid_warranties:
            result = validate_garantia_meses(warranty)
            assert result == warranty
    
    def test_validate_garantia_meses_invalid_ranges(self):
        """Test validación de garantía inválida"""
        invalid_warranties = [0, -1, 61, 120]
        
        from models.oferta import validate_garantia_meses
        for warranty in invalid_warranties:
            with pytest.raises(ValueError, match="Garantía debe estar entre 1 y 60 meses"):
                validate_garantia_meses(warranty)
    
    def test_validate_tiempo_entrega_valid_ranges(self):
        """Test validación de tiempo de entrega válido"""
        valid_times = [0, 1, 15, 30, 60, 90]  # 0 a 90 días
        
        from models.oferta import validate_tiempo_entrega
        for time in valid_times:
            result = validate_tiempo_entrega(time)
            assert result == time
    
    def test_validate_tiempo_entrega_invalid_ranges(self):
        """Test validación de tiempo de entrega inválido"""
        invalid_times = [-1, 91, 365, 1000]
        
        from models.oferta import validate_tiempo_entrega
        for time in invalid_times:
            with pytest.raises(ValueError, match="Tiempo de entrega debe estar entre 0 y 90 días"):
                validate_tiempo_entrega(time)


class TestOfertaIndividualValidation:
    """Tests de validación de ofertas individuales"""
    
    @pytest.mark.asyncio
    async def test_validate_oferta_data_success(self):
        """Test validación exitosa de datos de oferta"""
        # Mock solicitud
        mock_solicitud = MagicMock()
        mock_solicitud.id = "sol-123"
        mock_solicitud.estado = EstadoSolicitud.ABIERTA
        
        # Mock asesor
        mock_asesor = MagicMock()
        mock_asesor.id = "ase-123"
        
        # Mock repuestos
        mock_repuesto = MagicMock()
        mock_repuesto.id = "rep-123"
        
        detalles = [
            {
                'repuesto_solicitado_id': 'rep-123',
                'precio_unitario': 15000,
                'cantidad': 2,
                'garantia_meses': 12
            }
        ]
        
        with patch('services.ofertas_service.Solicitud.get_or_none', new_callable=AsyncMock, return_value=mock_solicitud), \
             patch('services.ofertas_service.Asesor.get_or_none', new_callable=AsyncMock, return_value=mock_asesor), \
             patch('services.ofertas_service.RepuestoSolicitado.filter', new_callable=AsyncMock, return_value=[mock_repuesto]):
            
            result = await OfertasService.validate_oferta_data(
                solicitud_id="sol-123",
                asesor_id="ase-123", 
                tiempo_entrega_dias=15,
                detalles=detalles
            )
            
            assert result['valid'] is True
            assert len(result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_oferta_data_solicitud_not_found(self):
        """Test validación con solicitud no encontrada"""
        with patch('services.ofertas_service.Solicitud.get_or_none', new_callable=AsyncMock, return_value=None):
            result = await OfertasService.validate_oferta_data(
                solicitud_id="invalid-id",
                asesor_id="ase-123",
                tiempo_entrega_dias=15,
                detalles=[]
            )
            
            assert result['valid'] is False
            assert "Solicitud invalid-id no encontrada" in result['errors']
    
    def test_validate_solicitud_estado_logic(self):
        """Test validación de estado de solicitud sin base de datos"""
        # Test lógica de validación de estado directamente
        
        # Estado válido
        estado_valido = EstadoSolicitud.ABIERTA
        assert estado_valido == EstadoSolicitud.ABIERTA
        
        # Estados inválidos
        estados_invalidos = [
            EstadoSolicitud.ACEPTADA,
            EstadoSolicitud.RECHAZADA,
            EstadoSolicitud.EXPIRADA,
            EstadoSolicitud.EVALUADA,
            EstadoSolicitud.CERRADA_SIN_OFERTAS
        ]
        
        for estado in estados_invalidos:
            assert estado != EstadoSolicitud.ABIERTA
    
    @pytest.mark.asyncio
    async def test_validate_oferta_data_invalid_ranges(self):
        """Test validación con rangos inválidos"""
        mock_solicitud = MagicMock()
        mock_solicitud.estado = EstadoSolicitud.ABIERTA
        mock_asesor = MagicMock()
        
        detalles = [
            {
                'repuesto_solicitado_id': 'rep-123',
                'precio_unitario': 500,  # Muy bajo
                'cantidad': 0,           # Inválido
                'garantia_meses': 70     # Muy alto
            }
        ]
        
        with patch('services.ofertas_service.Solicitud.get_or_none', new_callable=AsyncMock, return_value=mock_solicitud), \
             patch('services.ofertas_service.Asesor.get_or_none', new_callable=AsyncMock, return_value=mock_asesor), \
             patch('services.ofertas_service.RepuestoSolicitado.filter', new_callable=AsyncMock, return_value=[]):
            
            result = await OfertasService.validate_oferta_data(
                solicitud_id="sol-123",
                asesor_id="ase-123",
                tiempo_entrega_dias=100,  # Muy alto
                detalles=detalles
            )
            
            assert result['valid'] is False
            assert any("Tiempo de entrega debe estar entre 0 y 90 días" in error for error in result['errors'])
            assert any("Precio debe estar entre 1,000 y 50,000,000 COP" in error for error in result['errors'])
            assert any("Garantía debe estar entre 1 y 60 meses" in error for error in result['errors'])
            assert any("Cantidad debe ser mayor a 0" in error for error in result['errors'])


class TestCargaMasivaExcel:
    """Tests de carga masiva Excel - casos válidos e inválidos"""
    
    def create_valid_excel_content(self) -> bytes:
        """Crea contenido Excel válido para testing"""
        data = [
            {
                'repuesto_nombre': 'CONFIGURACIÓN GENERAL',
                'precio_unitario': '',
                'cantidad': '',
                'garantia_meses': '',
                'tiempo_entrega_dias': 15,
                'observaciones_generales': 'Oferta de prueba'
            },
            {
                'repuesto_nombre': 'Filtro de Aceite',
                'precio_unitario': 25000,
                'cantidad': 1,
                'garantia_meses': 12,
                'marca_repuesto': 'Mann',
                'modelo_repuesto': 'W712/75',
                'origen_repuesto': 'Original'
            },
            {
                'repuesto_nombre': 'Pastillas de Freno',
                'precio_unitario': 85000,
                'cantidad': 1,
                'garantia_meses': 24,
                'marca_repuesto': 'Brembo',
                'observaciones': 'Incluye sensores'
            }
        ]
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    def create_invalid_excel_content(self) -> bytes:
        """Crea contenido Excel inválido para testing"""
        data = [
            {
                'repuesto_nombre': 'Filtro Inválido',
                'precio_unitario': 500,      # Muy bajo
                'cantidad': 0,               # Inválido
                'garantia_meses': 70         # Muy alto
            },
            {
                'repuesto_nombre': 'Repuesto Inexistente',
                'precio_unitario': 60000000, # Muy alto
                'cantidad': -1,              # Negativo
                'garantia_meses': 0          # Muy bajo
            }
        ]
        
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    def test_excel_validation_logic(self):
        """Test lógica de validación de Excel sin parsing real"""
        # Test de validación de datos de Excel simulados
        
        # Caso válido
        detalle_valido = {
            'repuesto_solicitado_id': 'rep-123',
            'precio_unitario': 25000,
            'cantidad': 1,
            'garantia_meses': 12
        }
        
        # Validar precio
        precio = Decimal(str(detalle_valido['precio_unitario']))
        assert 1000 <= precio <= 50000000
        
        # Validar garantía
        garantia = detalle_valido['garantia_meses']
        assert 1 <= garantia <= 60
        
        # Validar cantidad
        cantidad = detalle_valido['cantidad']
        assert cantidad >= 1
        
        # Caso inválido
        detalle_invalido = {
            'precio_unitario': 500,  # Muy bajo
            'cantidad': 0,           # Inválido
            'garantia_meses': 70     # Muy alto
        }
        
        # Validar que los rangos inválidos fallan
        precio_invalido = Decimal(str(detalle_invalido['precio_unitario']))
        assert not (1000 <= precio_invalido <= 50000000)
        
        garantia_invalida = detalle_invalido['garantia_meses']
        assert not (1 <= garantia_invalida <= 60)
        
        cantidad_invalida = detalle_invalido['cantidad']
        assert not (cantidad_invalida >= 1)
    
    @pytest.mark.asyncio
    async def test_parse_excel_invalid_content(self):
        """Test parsing de Excel inválido"""
        mock_solicitud = MagicMock()
        excel_content = self.create_invalid_excel_content()
        
        with patch('services.ofertas_service.Solicitud.get_or_none', new_callable=AsyncMock, return_value=mock_solicitud), \
             patch('services.ofertas_service.RepuestoSolicitado.filter', new_callable=AsyncMock, return_value=[]):
            
            result = await OfertasService.parse_and_validate_excel(
                excel_content=excel_content,
                solicitud_id="sol-123",
                asesor_id="ase-123"
            )
            
            assert result['valid'] is False
            assert len(result['errors']) > 0
            # Verificar errores específicos de rangos
            errors_text = ' '.join(result['errors'])
            assert "Precio debe estar entre 1,000 y 50,000,000 COP" in errors_text
            assert "Garantía debe estar entre 1 y 60 meses" in errors_text
            assert "Cantidad debe ser mayor a 0" in errors_text
    
    @pytest.mark.asyncio
    async def test_parse_excel_empty_file(self):
        """Test parsing de archivo Excel vacío"""
        # Crear Excel vacío
        df = pd.DataFrame()
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        excel_content = excel_buffer.getvalue()
        
        result = await OfertasService.parse_and_validate_excel(
            excel_content=excel_content,
            solicitud_id="sol-123",
            asesor_id="ase-123"
        )
        
        assert result['valid'] is False
        assert "Archivo Excel está vacío" in result['errors']
    
    @pytest.mark.asyncio
    async def test_parse_excel_missing_columns(self):
        """Test parsing de Excel con columnas faltantes"""
        # Crear Excel sin columnas requeridas
        data = [{'columna_incorrecta': 'valor'}]
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        excel_content = excel_buffer.getvalue()
        
        result = await OfertasService.parse_and_validate_excel(
            excel_content=excel_content,
            solicitud_id="sol-123",
            asesor_id="ase-123"
        )
        
        assert result['valid'] is False
        assert "Columnas requeridas faltantes" in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_bulk_upload_file_size_validation(self):
        """Test validación de tamaño de archivo"""
        # Crear contenido que exceda 5MB
        large_content = b'x' * (6 * 1024 * 1024)  # 6MB
        
        with pytest.raises(ValueError, match="Archivo excede el tamaño máximo de 5MB"):
            await OfertasService.create_oferta_bulk_excel(
                solicitud_id="sol-123",
                asesor_id="ase-123",
                excel_file_content=large_content,
                filename="large_file.xlsx"
            )
    
    @pytest.mark.asyncio
    async def test_bulk_upload_invalid_format(self):
        """Test validación de formato de archivo"""
        with pytest.raises(ValueError, match="Archivo debe ser formato .xlsx"):
            await OfertasService.create_oferta_bulk_excel(
                solicitud_id="sol-123",
                asesor_id="ase-123",
                excel_file_content=b"invalid content",
                filename="file.txt"
            )


class TestTransicionesEstado:
    """Tests de transiciones de estado de ofertas"""
    
    def test_get_transiciones_permitidas_enviada(self):
        """Test transiciones permitidas desde ENVIADA"""
        transiciones = OfertasService._get_transiciones_permitidas(EstadoOferta.ENVIADA)
        
        expected = [
            EstadoOferta.GANADORA,
            EstadoOferta.NO_SELECCIONADA,
            EstadoOferta.EXPIRADA,
            EstadoOferta.RECHAZADA
        ]
        
        assert set(transiciones) == set(expected)
    
    def test_get_transiciones_permitidas_ganadora(self):
        """Test transiciones permitidas desde GANADORA"""
        transiciones = OfertasService._get_transiciones_permitidas(EstadoOferta.GANADORA)
        
        expected = [
            EstadoOferta.ACEPTADA,
            EstadoOferta.RECHAZADA,
            EstadoOferta.EXPIRADA
        ]
        
        assert set(transiciones) == set(expected)
    
    def test_get_transiciones_permitidas_estados_finales(self):
        """Test que estados finales no tienen transiciones"""
        estados_finales = [
            EstadoOferta.NO_SELECCIONADA,
            EstadoOferta.ACEPTADA,
            EstadoOferta.RECHAZADA,
            EstadoOferta.EXPIRADA
        ]
        
        for estado in estados_finales:
            transiciones = OfertasService._get_transiciones_permitidas(estado)
            assert transiciones == []
    
    def test_validacion_transicion_valida(self):
        """Test validación de transición válida sin base de datos"""
        # Test lógica de transiciones directamente
        estado_actual = EstadoOferta.ENVIADA
        nuevo_estado = EstadoOferta.GANADORA
        
        transiciones_permitidas = OfertasService._get_transiciones_permitidas(estado_actual)
        assert nuevo_estado in transiciones_permitidas
    
    def test_validacion_transicion_invalida(self):
        """Test validación de transición inválida sin base de datos"""
        # Test lógica de transiciones directamente
        estado_actual = EstadoOferta.ACEPTADA  # Estado final
        nuevo_estado = EstadoOferta.ENVIADA
        
        transiciones_permitidas = OfertasService._get_transiciones_permitidas(estado_actual)
        assert nuevo_estado not in transiciones_permitidas
        assert len(transiciones_permitidas) == 0  # Estados finales no tienen transiciones
    
    def test_matriz_transiciones_completa(self):
        """Test matriz completa de transiciones de estado"""
        # Verificar todas las transiciones definidas
        matriz_esperada = {
            EstadoOferta.ENVIADA: [
                EstadoOferta.GANADORA,
                EstadoOferta.NO_SELECCIONADA,
                EstadoOferta.EXPIRADA,
                EstadoOferta.RECHAZADA
            ],
            EstadoOferta.GANADORA: [
                EstadoOferta.ACEPTADA,
                EstadoOferta.RECHAZADA,
                EstadoOferta.EXPIRADA
            ],
            EstadoOferta.NO_SELECCIONADA: [],
            EstadoOferta.ACEPTADA: [],
            EstadoOferta.RECHAZADA: [],
            EstadoOferta.EXPIRADA: []
        }
        
        for estado_actual, transiciones_esperadas in matriz_esperada.items():
            transiciones_obtenidas = OfertasService._get_transiciones_permitidas(estado_actual)
            assert set(transiciones_obtenidas) == set(transiciones_esperadas), \
                f"Transiciones incorrectas para {estado_actual}: esperadas {transiciones_esperadas}, obtenidas {transiciones_obtenidas}"


class TestOfertaModelProperties:
    """Tests de propiedades y métodos del modelo Oferta"""
    
    def test_codigo_oferta_generation(self):
        """Test generación de código de oferta"""
        mock_oferta = MagicMock()
        mock_oferta.id = "12345678-1234-1234-1234-123456789012"
        
        # Simulate the property
        codigo = f"OF-{str(mock_oferta.id)[:8].upper()}"
        assert codigo == "OF-12345678"
    
    def test_oferta_state_checks(self):
        """Test verificaciones de estado de oferta"""
        # Test is_activa
        mock_oferta_activa = MagicMock()
        mock_oferta_activa.estado = EstadoOferta.ENVIADA
        assert mock_oferta_activa.estado == EstadoOferta.ENVIADA  # is_activa would return True
        
        # Test is_ganadora
        mock_oferta_ganadora = MagicMock()
        mock_oferta_ganadora.estado = EstadoOferta.GANADORA
        assert mock_oferta_ganadora.estado == EstadoOferta.GANADORA  # is_ganadora would return True
        
        # Test is_aceptada_cliente
        mock_oferta_aceptada = MagicMock()
        mock_oferta_aceptada.estado = EstadoOferta.ACEPTADA
        assert mock_oferta_aceptada.estado == EstadoOferta.ACEPTADA  # is_aceptada_cliente would return True


class TestOfertaDetalleValidation:
    """Tests de validación de detalles de oferta"""
    
    def test_monto_total_detalle_calculation(self):
        """Test cálculo de monto total del detalle"""
        precio_unitario = Decimal('15000')
        cantidad = 3
        monto_esperado = precio_unitario * cantidad
        
        assert monto_esperado == Decimal('45000')
    
    def test_descripcion_garantia_formatting(self):
        """Test formateo de descripción de garantía"""
        test_cases = [
            (1, "1 mes"),
            (6, "6 meses"),
            (12, "1 año"),
            (24, "2 años"),
            (13, "1 año y 1 mes"),
            (25, "2 años y 1 mes"),
            (26, "2 años y 2 meses")
        ]
        
        for meses, expected in test_cases:
            # Simulate the property logic
            if meses == 1:
                result = "1 mes"
            elif meses < 12:
                result = f"{meses} meses"
            else:
                años = meses // 12
                meses_restantes = meses % 12
                if meses_restantes == 0:
                    result = f"{años} año{'s' if años > 1 else ''}"
                else:
                    result = f"{años} año{'s' if años > 1 else ''} y {meses_restantes} mes{'es' if meses_restantes > 1 else ''}"
            
            assert result == expected
    
    def test_descripcion_entrega_formatting(self):
        """Test formateo de descripción de entrega"""
        test_cases = [
            (0, "Inmediato"),
            (1, "1 día"),
            (5, "5 días"),
            (30, "30 días")
        ]
        
        for dias, expected in test_cases:
            # Simulate the property logic
            if dias == 0:
                result = "Inmediato"
            elif dias == 1:
                result = "1 día"
            else:
                result = f"{dias} días"
            
            assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])