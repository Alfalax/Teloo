"""
PDF Generator Service for TeLOO V3
Generates professional PDF documents for client offers
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from models.solicitud import Solicitud
from models.oferta import AdjudicacionRepuesto

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """Service for generating PDF documents"""
    
    @staticmethod
    async def generar_pdf_ofertas_ganadoras(
        solicitud_id: str,
        incluir_logo: bool = True
    ) -> BytesIO:
        """
        Generate PDF with winning offers for client
        
        Args:
            solicitud_id: ID of the solicitud
            incluir_logo: Whether to include TeLOO logo
            
        Returns:
            BytesIO with PDF content
        """
        try:
            # Get solicitud with all relationships
            solicitud = await Solicitud.get(id=solicitud_id).prefetch_related(
                'cliente__usuario',
                'municipio',
                'repuestos_solicitados',
                'adjudicaciones__oferta__asesor__usuario',
                'adjudicaciones__repuesto_solicitado',
                'adjudicaciones__oferta_detalle'
            )
            
            # Get adjudications
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud=solicitud
            ).prefetch_related(
                'oferta__asesor__usuario',
                'repuesto_solicitado',
                'oferta_detalle'
            ).order_by('repuesto_solicitado__nombre')
            
            if not adjudicaciones:
                raise ValueError("No hay adjudicaciones para generar PDF")
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=0.75*inch
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a56db'),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#6b7280'),
                spaceAfter=6,
                alignment=TA_CENTER
            )
            
            section_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # TODO: Add logo if available
            # if incluir_logo:
            #     logo = Image('path/to/logo.png', width=2*inch, height=0.5*inch)
            #     elements.append(logo)
            #     elements.append(Spacer(1, 0.3*inch))
            
            # Title
            elements.append(Paragraph("PROPUESTA COMERCIAL", title_style))
            elements.append(Paragraph(f"Solicitud #{solicitud.codigo_solicitud}", subtitle_style))
            elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
            elements.append(Spacer(1, 0.3*inch))
            
            # Client information section
            elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", section_style))
            
            # Get vehicle info from first repuesto (all should have same vehicle)
            linea_str = 'N/A'
            if solicitud.repuestos_solicitados:
                primer_repuesto = solicitud.repuestos_solicitados[0]
                marca = primer_repuesto.marca_vehiculo or ''
                linea = primer_repuesto.linea_vehiculo or ''
                anio = str(primer_repuesto.anio_vehiculo) if primer_repuesto.anio_vehiculo else ''
                linea_str = f"{marca} {linea} {anio}".strip() or 'N/A'
            
            client_data = [
                ['Nombre:', solicitud.cliente.usuario.nombre_completo],
                ['Teléfono:', solicitud.cliente.usuario.telefono or 'N/A'],
                ['Ciudad:', solicitud.municipio.municipio if solicitud.municipio else 'N/A'],
                ['Línea:', linea_str]
            ]
            
            client_table = Table(client_data, colWidths=[1.5*inch, 4.5*inch])
            client_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#6b7280')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(client_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Winning offers section
            elements.append(Paragraph("OFERTAS GANADORAS", section_style))
            
            # Table headers
            table_data = [[
                '#',
                'Repuesto',
                'Asesor',
                'Precio',
                'Entrega',
                'Garantía'
            ]]
            
            # Add adjudications
            for idx, adj in enumerate(adjudicaciones, 1):
                table_data.append([
                    str(idx),
                    adj.repuesto_solicitado.nombre,
                    adj.oferta.asesor.usuario.nombre_completo,
                    f"${adj.precio_adjudicado:,.0f}",
                    f"{adj.tiempo_entrega_adjudicado} días",
                    f"{adj.garantia_adjudicada} meses"
                ])
            
            # Add total row
            monto_total = sum(
                adj.precio_adjudicado * adj.cantidad_adjudicada 
                for adj in adjudicaciones
            )
            table_data.append([
                '',
                '',
                '',
                'TOTAL:',
                f"${monto_total:,.0f}",
                ''
            ])
            
            # Create table
            offers_table = Table(
                table_data,
                colWidths=[0.4*inch, 2*inch, 1.8*inch, 1*inch, 0.8*inch, 0.8*inch]
            )
            
            offers_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),
                ('ALIGN', (3, 1), (-1, -2), 'RIGHT'),
                ('VALIGN', (0, 1), (-1, -2), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9fafb')]),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 1), (-1, -2), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('ALIGN', (3, -1), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, -1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1a56db')),
            ]))
            
            elements.append(offers_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Important note
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#6b7280'),
                leftIndent=20,
                rightIndent=20,
                spaceAfter=6
            )
            
            elements.append(Paragraph("NOTA IMPORTANTE:", section_style))
            elements.append(Paragraph(
                "Los precios pueden ser negociables cuando el asesor te contacte.",
                note_style
            ))
            elements.append(Paragraph(
                f"Válido por 24 horas desde {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                note_style
            ))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF content
            buffer.seek(0)
            
            logger.info(f"PDF generado exitosamente para solicitud {solicitud.codigo_solicitud}")
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generando PDF para solicitud {solicitud_id}: {e}")
            raise
    
    @staticmethod
    async def calcular_metricas_ofertas(solicitud_id: str) -> Dict[str, Any]:
        """
        Calculate metrics for offers (asesores contacted, savings)
        
        Args:
            solicitud_id: ID of the solicitud
            
        Returns:
            Dict with metrics
        """
        try:
            from models.oferta import Oferta, OfertaDetalle
            
            # Get all offers for this solicitud
            ofertas = await Oferta.filter(
                solicitud_id=solicitud_id
            ).prefetch_related('asesor', 'detalles')
            
            # Count unique asesores
            asesores_contactados = len(set(oferta.asesor.id for oferta in ofertas))
            
            # Get adjudications
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud_id=solicitud_id
            ).prefetch_related('repuesto_solicitado', 'oferta_detalle')
            
            # Calculate savings (difference between highest and winning prices)
            ahorro_total = Decimal('0')
            
            for adj in adjudicaciones:
                repuesto_id = adj.repuesto_solicitado.id
                
                # Get all prices for this repuesto
                detalles = await OfertaDetalle.filter(
                    repuesto_solicitado_id=repuesto_id,
                    oferta__solicitud_id=solicitud_id
                ).all()
                
                if detalles:
                    precios = [d.precio_unitario for d in detalles]
                    precio_maximo = max(precios)
                    precio_ganador = adj.precio_adjudicado
                    
                    ahorro_repuesto = (precio_maximo - precio_ganador) * adj.cantidad_adjudicada
                    ahorro_total += ahorro_repuesto
            
            # Calculate savings percentage
            monto_total = sum(
                adj.precio_adjudicado * adj.cantidad_adjudicada 
                for adj in adjudicaciones
            )
            
            porcentaje_ahorro = 0
            if monto_total > 0:
                porcentaje_ahorro = (ahorro_total / (monto_total + ahorro_total)) * 100
            
            return {
                'asesores_contactados': asesores_contactados,
                'ahorro_obtenido': float(ahorro_total),
                'porcentaje_ahorro': float(porcentaje_ahorro),
                'monto_total': float(monto_total)
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas para solicitud {solicitud_id}: {e}")
            return {
                'asesores_contactados': 0,
                'ahorro_obtenido': 0,
                'porcentaje_ahorro': 0,
                'monto_total': 0
            }
