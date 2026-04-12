"""
Documentation PDF generator for the Client Segmentation product.
Run with: C:/Users/mpsua/anaconda3/envs/dl/python.exe generate_docs.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.colors import HexColor
import os

# ── Colour palette ─────────────────────────────────────────────────────────────
BLACK       = HexColor('#0a0a0a')
ACCENT      = HexColor('#1a1a2e')
ACCENT_SOFT = HexColor('#2f4b7c')
GRAY_BG     = HexColor('#f5f5f5')
GRAY_BORDER = HexColor('#cccccc')
GREEN       = HexColor('#2a7a3b')
BLUE        = HexColor('#003f5c')
PURPLE      = HexColor('#665191')
PINK        = HexColor('#d45087')
ORANGE      = HexColor('#ffa600')
WHITE       = HexColor('#ffffff')

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ── Custom doc template with header/footer ─────────────────────────────────────
class DocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(MARGIN, MARGIN + 1.2*cm, PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN - 1.8*cm, id='main')
        self.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=self._on_page)])

    def _on_page(self, canvas, doc):
        canvas.saveState()
        # Bottom line + page number
        canvas.setStrokeColor(GRAY_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, MARGIN + 0.8*cm, PAGE_W - MARGIN, MARGIN + 0.8*cm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#888888'))
        canvas.drawString(MARGIN, MARGIN + 0.3*cm, 'Client Segmentation Platform — Documentación Técnica')
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN + 0.3*cm, f'Página {doc.page}')
        canvas.restoreState()


# ── Style definitions ──────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def make_style(name, parent='Normal', **kwargs):
    s = ParagraphStyle(name, parent=base[parent], **kwargs)
    return s

S = {
    'title': make_style('DocTitle', fontSize=26, fontName='Helvetica-Bold',
                        textColor=BLACK, spaceAfter=6, leading=32),
    'subtitle': make_style('DocSubtitle', fontSize=13, fontName='Helvetica',
                           textColor=HexColor('#555555'), spaceAfter=4, leading=18),
    'h1': make_style('H1', fontSize=16, fontName='Helvetica-Bold',
                     textColor=ACCENT, spaceBefore=22, spaceAfter=8, leading=22),
    'h2': make_style('H2', fontSize=12, fontName='Helvetica-Bold',
                     textColor=ACCENT_SOFT, spaceBefore=14, spaceAfter=6, leading=16),
    'h3': make_style('H3', fontSize=10.5, fontName='Helvetica-Bold',
                     textColor=BLACK, spaceBefore=10, spaceAfter=4, leading=14),
    'body': make_style('Body', fontSize=10, fontName='Helvetica',
                       textColor=BLACK, spaceAfter=6, leading=15, alignment=TA_JUSTIFY),
    'bullet': make_style('Bullet', fontSize=10, fontName='Helvetica',
                         textColor=BLACK, spaceAfter=4, leading=14,
                         leftIndent=16, bulletIndent=4),
    'bullet2': make_style('Bullet2', fontSize=9.5, fontName='Helvetica',
                          textColor=HexColor('#333333'), spaceAfter=3, leading=13,
                          leftIndent=32, bulletIndent=20),
    'code': make_style('Code', fontSize=8.5, fontName='Courier',
                       textColor=HexColor('#1a1a1a'), backColor=GRAY_BG,
                       spaceAfter=4, leading=12, leftIndent=12, rightIndent=12,
                       borderPadding=(4, 6, 4, 6)),
    'note': make_style('Note', fontSize=9.5, fontName='Helvetica-Oblique',
                       textColor=HexColor('#555555'), spaceAfter=6, leading=14,
                       leftIndent=10),
    'badge': make_style('Badge', fontSize=9, fontName='Helvetica-Bold',
                        textColor=WHITE),
    'toc_entry': make_style('TocEntry', fontSize=10, fontName='Helvetica',
                            textColor=ACCENT_SOFT, spaceAfter=3, leading=14),
}

def B(text):   return f'<b>{text}</b>'
def I(text):   return f'<i>{text}</i>'
def C(text, c='#2f4b7c'): return f'<font color="{c}">{text}</font>'
def MONO(text): return f'<font face="Courier">{text}</font>'

def p(text, style='body'):    return Paragraph(text, S[style])
def sp(h=0.3):                return Spacer(1, h * cm)
def hr(color=GRAY_BORDER):    return HRFlowable(width='100%', thickness=0.5, color=color, spaceAfter=6)
def pb():                     return PageBreak()

def bullet(text, level=1):
    sty = 'bullet' if level == 1 else 'bullet2'
    prefix = '•' if level == 1 else '◦'
    return Paragraph(f'{prefix} {text}', S[sty])

def section_header(num, title, color=ACCENT):
    """Colored section header bar."""
    return Table(
        [[Paragraph(f'{num}. {title}', ParagraphStyle('sh', fontName='Helvetica-Bold',
            fontSize=14, textColor=WHITE, leading=18))]],
        colWidths=[PAGE_W - 2*MARGIN],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), color),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 14),
            ('RIGHTPADDING',  (0,0), (-1,-1), 14),
        ])
    )

def info_box(text, bg=GRAY_BG, border=GRAY_BORDER):
    return Table(
        [[Paragraph(text, S['body'])]],
        colWidths=[PAGE_W - 2*MARGIN],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), bg),
            ('BOX',           (0,0), (-1,-1), 0.8, border),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 12),
            ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ])
    )

def method_card(title, tag, tag_color, body_paragraphs):
    """Card for each segmentation method."""
    header = Table(
        [[Paragraph(B(title), ParagraphStyle('mct', fontName='Helvetica-Bold', fontSize=11,
                                              textColor=WHITE, leading=15)),
          Paragraph(tag, ParagraphStyle('mctag', fontName='Helvetica-Bold', fontSize=9,
                                         textColor=WHITE, leading=13, alignment=TA_CENTER))]],
        colWidths=[PAGE_W - 2*MARGIN - 3*cm, 2.8*cm],
        style=TableStyle([
            ('BACKGROUND',    (0,0), (0,0), tag_color),
            ('BACKGROUND',    (1,0), (1,0), tag_color.clone(alpha=0.75) if hasattr(tag_color,'clone') else tag_color),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (0,0), 12),
            ('RIGHTPADDING',  (1,0), (1,0), 8),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ])
    )
    inner = [header] + body_paragraphs
    return Table(
        [[inner]],
        colWidths=[PAGE_W - 2*MARGIN],
        style=TableStyle([
            ('BOX',        (0,0), (-1,-1), 1, GRAY_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING',   (0,0), (-1,-1), 0),
            ('RIGHTPADDING',  (0,0), (-1,-1), 0),
        ])
    )


# ── Document assembly ──────────────────────────────────────────────────────────
def build():
    out = os.path.join(os.path.dirname(__file__), 'product', 'Documentacion_Tecnica_ClientSegmentation.pdf')
    doc = DocTemplate(out, pagesize=A4,
                      leftMargin=MARGIN, rightMargin=MARGIN,
                      topMargin=MARGIN + 0.5*cm, bottomMargin=MARGIN + 1.5*cm)
    story = []

    # ── PORTADA ────────────────────────────────────────────────────────────────
    story += [
        sp(3),
        p('Client Segmentation Platform', 'title'),
        p('Documentación Técnica del Sistema', 'subtitle'),
        sp(0.3),
        hr(ACCENT_SOFT),
        sp(0.3),
        p(I('Repositorio: product/ — Backend FastAPI + Frontend React'), 'note'),
        sp(6),
    ]

    # ── ÍNDICE ─────────────────────────────────────────────────────────────────
    story += [
        p(B('Índice de contenidos'), 'h1'),
        hr(),
        p('1. Arquitectura y tecnologías utilizadas', 'toc_entry'),
        p('2. Métodos de segmentación implementados', 'toc_entry'),
        p('3. Tratamiento de valores nulos y decisiones de calidad de datos', 'toc_entry'),
        p('4. Dashboards y visualizaciones por método', 'toc_entry'),
        p('5. Integración con Google BigQuery y hoja de ruta cloud', 'toc_entry'),
        pb(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — ARQUITECTURA Y TECNOLOGÍAS
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        section_header('1', 'Arquitectura y tecnologías utilizadas', BLUE),
        sp(0.4),
        p('La plataforma sigue una arquitectura cliente-servidor clásica con separación completa '
          'entre frontend y backend. Ambas capas se ejecutan de forma independiente y se comunican '
          'exclusivamente mediante una API REST.', 'body'),
        sp(0.3),
    ]

    story += [
        p(B('1.1 Backend — Python / FastAPI'), 'h2'),
        p('El servidor está construido sobre <b>FastAPI</b>, un framework web moderno para Python '
          'basado en estándares OpenAPI y tipado estático (Pydantic). Se sirve mediante '
          '<b>Uvicorn</b>, un servidor ASGI de alto rendimiento. La elección de FastAPI frente a '
          'alternativas como Flask o Django REST se justifica por su validación automática de '
          'esquemas, documentación interactiva generada automáticamente (<i>/docs</i>) y '
          'rendimiento superior en operaciones asíncronas.', 'body'),
        sp(0.2),
    ]

    backend_libs = [
        ['Librería', 'Versión mín.', 'Uso en el proyecto'],
        ['fastapi', '0.111.0', 'Framework web principal — enrutamiento, validación, OpenAPI'],
        ['uvicorn[standard]', '0.29.0', 'Servidor ASGI — sirve la app FastAPI'],
        ['python-multipart', '0.0.9', 'Parsing de formularios y subida de archivos'],
        ['pandas', '2.0.0', 'Manipulación y transformación del DataFrame en todos los pasos'],
        ['numpy', '1.24.0', 'Operaciones numéricas; soporte a scikit-learn'],
        ['scikit-learn', '1.3.0', 'Clustering (K-Means, DBSCAN), métricas (Silhouette, etc.)'],
        ['openpyxl', '3.1.0', 'Lectura de archivos Excel (.xlsx, .xls)'],
        ['google-cloud-bigquery', '3.11.0', 'Ejecución de consultas SQL sobre BigQuery'],
        ['google-auth', '2.22.0', 'Autenticación con cuenta de servicio de Google Cloud'],
        ['db-dtypes', '1.1.1', 'Conversión de tipos de datos propios de BigQuery a pandas'],
        ['pydantic', '(con FastAPI)', 'Validación y serialización de modelos de entrada/salida'],
    ]
    t = Table(backend_libs,
              colWidths=[4.2*cm, 2.8*cm, PAGE_W - 2*MARGIN - 7*cm],
              style=TableStyle([
                  ('BACKGROUND',    (0,0), (-1,0), ACCENT_SOFT),
                  ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                  ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                  ('FONTSIZE',      (0,0), (-1,-1), 8.5),
                  ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
                  ('GRID',          (0,0), (-1,-1), 0.4, GRAY_BORDER),
                  ('TOPPADDING',    (0,0), (-1,-1), 5),
                  ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                  ('LEFTPADDING',   (0,0), (-1,-1), 8),
                  ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
              ]))
    story += [t, sp(0.4)]

    story += [
        p(B('Estructura del backend'), 'h3'),
        p('El código se organiza en cuatro capas bien definidas:', 'body'),
        bullet(f'{B("routers/")} — Capa de transporte HTTP. Define los endpoints REST y delega '
               'la lógica a los servicios. Hay cuatro routers: '
               f'{MONO("upload")}, {MONO("mapping")}, {MONO("cleaning")}, {MONO("segmentation")}.'),
        bullet(f'{B("services/")} — Lógica de negocio: parseado de archivos, mapeo de columnas, '
               'limpieza, agregación RFM, algoritmos de segmentación y conector BigQuery.'),
        bullet(f'{B("models/")} — Modelos Pydantic para validar las peticiones y estructurar las respuestas.'),
        bullet(f'{B("core/")} — Sesión en memoria ({MONO("session_store.py")}) y clases de excepción personalizadas.'),
        bullet(f'{B("utils/")} — Utilidades de clustering (selección de k óptimo) y exportación CSV.'),
        sp(0.3),
    ]

    story += [
        p(B('Gestión de sesiones'), 'h3'),
        p('Cada proceso de segmentación genera un <b>session_id</b> único (UUID). La sesión almacena '
          'en memoria los DataFrames intermedios: datos crudos, datos mapeados, datos limpios y '
          'resultados de segmentación. Este diseño permite que el frontend avance paso a paso sin '
          're-enviar los datos en cada petición.', 'body'),
        info_box('⚠ El almacén de sesiones es un diccionario en memoria (diseño de prototipo). '
                 'En producción se sustituiría por Redis u otro almacén distribuido.'),
        sp(0.3),
    ]

    story += [
        p(B('1.2 Frontend — React + Vite'), 'h2'),
        p('La interfaz es una <b>Single Page Application (SPA)</b> construida con React 18. '
          'El scaffolding y el servidor de desarrollo utilizan <b>Vite</b>, que ofrece HMR '
          '(Hot Module Replacement) instantáneo y builds de producción optimizados.', 'body'),
        sp(0.2),
    ]

    frontend_libs = [
        ['Librería / Herramienta', 'Versión', 'Función'],
        ['react + react-dom', '^18.3.1', 'Framework UI — componentes, hooks, ciclo de vida'],
        ['vite + @vitejs/plugin-react', '^5.3.1', 'Build tool — dev server, HMR, bundle optimizado'],
        ['zustand', '^4.5.2', 'Gestión de estado global (wizard, sesión, idioma)'],
        ['axios', '^1.7.2', 'Cliente HTTP para llamadas a la API backend'],
        ['recharts', '^2.15.4', 'Librería de gráficos SVG (barras, dispersión, Pareto, pie)'],
    ]
    t2 = Table(frontend_libs,
               colWidths=[5*cm, 2.5*cm, PAGE_W - 2*MARGIN - 7.5*cm],
               style=TableStyle([
                   ('BACKGROUND',    (0,0), (-1,0), ACCENT_SOFT),
                   ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                   ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                   ('FONTSIZE',      (0,0), (-1,-1), 8.5),
                   ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
                   ('GRID',          (0,0), (-1,-1), 0.4, GRAY_BORDER),
                   ('TOPPADDING',    (0,0), (-1,-1), 5),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                   ('LEFTPADDING',   (0,0), (-1,-1), 8),
                   ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
               ]))
    story += [t2, sp(0.4)]

    story += [
        p(B('Arquitectura del estado — Zustand'), 'h3'),
        p('El estado de la aplicación se divide en tres stores independientes:', 'body'),
        bullet(f'{B("wizardStore")} — Estado central del flujo: paso actual, método elegido, '
               'resultados de cada etapa. Cuando el usuario retrocede un paso, el store '
               'limpia automáticamente los datos posteriores para forzar la re-ejecución.'),
        bullet(f'{B("sessionStore")} — Persiste el session_id en localStorage para sobrevivir '
               'recargas de página.'),
        bullet(f'{B("uiStore")} — Estado de la interfaz: idioma activo (inglés / español).'),
        sp(0.2),
        p(B('Internacionalización (i18n)'), 'h3'),
        p(f'Toda la interfaz es bilingüe (inglés / español de España). Las cadenas de texto se '
          f'almacenan en un objeto de traducciones ({MONO("translations.js")}) con las claves '
          f'de ambos idiomas. El hook {MONO("useT()")} recupera el objeto del idioma activo '
          f'desde {MONO("uiStore")}. El botón de cambio de idioma está situado en la cabecera, '
          'junto al botón de "Empezar de nuevo".', 'body'),
        sp(0.2),
        p(B('Flujo de la aplicación — 6 pasos'), 'h3'),
    ]

    steps = [
        ['Paso', 'Nombre', 'Descripción'],
        ['1', 'Método', 'Selección del algoritmo de segmentación'],
        ['2', 'Datos', 'Carga del dataset (archivo o BigQuery)'],
        ['3', 'Mapeo', 'Asignación de columnas del archivo a las métricas del sistema'],
        ['4', 'Limpieza', 'Filtros de calidad: nulos, negativos, duplicados'],
        ['5', 'Configuración', 'Parámetros específicos del método elegido'],
        ['6', 'Resultados', 'Tabla de segmentos, descarga CSV, dashboard interactivo'],
    ]
    t3 = Table(steps,
               colWidths=[1.5*cm, 3.5*cm, PAGE_W - 2*MARGIN - 5*cm],
               style=TableStyle([
                   ('BACKGROUND',    (0,0), (-1,0), ACCENT_SOFT),
                   ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                   ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                   ('FONTSIZE',      (0,0), (-1,-1), 9),
                   ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
                   ('GRID',          (0,0), (-1,-1), 0.4, GRAY_BORDER),
                   ('TOPPADDING',    (0,0), (-1,-1), 5),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                   ('LEFTPADDING',   (0,0), (-1,-1), 8),
                   ('ALIGN',         (0,0), (0,-1), 'CENTER'),
                   ('FONTNAME',      (0,1), (0,-1), 'Helvetica-Bold'),
                   ('TEXTCOLOR',     (0,1), (0,-1), ACCENT_SOFT),
               ]))
    story += [t3, pb()]

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — MÉTODOS DE SEGMENTACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        section_header('2', 'Métodos de segmentación implementados', ACCENT_SOFT),
        sp(0.4),
        p('La plataforma implementa cuatro métodos de segmentación de clientes, cada uno con '
          'un flujo de configuración, parámetros y dashboard propios. El usuario elige el '
          'método en el Paso 1 y a partir de ese momento toda la experiencia (etiquetas, '
          'opciones disponibles, gráficos) se adapta automáticamente.', 'body'),
        sp(0.4),
    ]

    # ── 2.1 RFM Quintiles ─────────────────────────────────────────────────────
    story += [
        p(B('2.1 RFM Quintiles'), 'h2'),
        p('<b>Concepto:</b> Divide a los clientes en cinco grupos (quintiles 1–5) según cada una '
          'de las tres métricas RFM y los asigna a segmentos nombrados mediante reglas de '
          'expresiones regulares.', 'body'),
        p('<b>Métricas:</b>', 'body'),
        bullet(f'{B("R — Recency:")} días desde la última compra. '
               'Puntuación 5 = cliente muy reciente, 1 = lleva mucho tiempo sin comprar.'),
        bullet(f'{B("F — Frequency:")} número de pedidos únicos. '
               'Puntuación 5 = compra con mucha frecuencia.'),
        bullet(f'{B("M — Monetary:")} gasto total acumulado. '
               'Puntuación 5 = cliente de alto valor.'),
        sp(0.2),
        p('<b>Proceso:</b>', 'body'),
        bullet('Se calculan los quintiles de cada métrica sobre el conjunto completo de clientes.'),
        bullet('Se concatenan las tres puntuaciones en un código RFM (p. ej. "543").'),
        bullet('Se recorre la lista de patrones de segmento en orden. El primer patrón que '
               'coincide con el código RFM del cliente determina su segmento.'),
        bullet('Los patrones usan sintaxis de expresión regular acotada: '
               f'{MONO("[4-5]")} significa puntuación 4 ó 5, {MONO("[1]")} significa exactamente 1.'),
        sp(0.2),
        p('<b>Segmentos predeterminados (15):</b> Champions, Loyal Customers, Potential Loyalists, '
          'Recent Customers, Occasional Customers, Potential Customers, Economic Loyalists, '
          'Risky Customers, Nearly Lost, Need Attention, Average Customers, Non Active, '
          'Sleeping, New Customers, Lost.', 'body'),
        sp(0.2),
        p('<b>Parámetros configurables en el Paso 5:</b>', 'body'),
        bullet('El usuario puede <b>editar el nombre</b> de cualquier segmento predeterminado.'),
        bullet('Puede <b>modificar el patrón</b> R/F/M de cada segmento directamente en la tabla.'),
        bullet('Puede <b>desactivar segmentos</b> que no le resulten relevantes (checkbox).'),
        bullet('Puede <b>añadir segmentos nuevos</b> definiendo un nombre y sus rangos R/F/M.'),
        bullet('El orden importa: se aplica el primer patrón que coincida (first-match wins).'),
        sp(0.3),
    ]

    # ── 2.2 RFM K-Means ───────────────────────────────────────────────────────
    story += [
        p(B('2.2 RFM K-Means / DBSCAN'), 'h2'),
        p('<b>Concepto:</b> En lugar de reglas fijas, agrupa clientes mediante algoritmos de '
          'clustering no supervisado sobre el espacio tridimensional RFM. Los segmentos emergen '
          'de los propios datos, sin etiquetas predefinidas.', 'body'),
        p('<b>Pre-procesamiento:</b> Las tres métricas RFM se normalizan con '
          f'{MONO("StandardScaler")} para que ninguna dimensión domine por escala.', 'body'),
        sp(0.2),
        p('<b>Algoritmo K-Means:</b>', 'body'),
        bullet('Se prueban todos los valores de k en el rango [k_min, k_max] configurado.'),
        bullet(f'Para cada k se calculan cuatro métricas de calidad: {B("WCSS")} (inercia), '
               f'{B("Silhouette Score")}, {B("Davies-Bouldin Index")} y '
               f'{B("Calinski-Harabasz Score")}.'),
        bullet(f'El método de selección automática de k puede ser: {B("combined")} '
               '(40% Silhouette + 30% Davies-Bouldin invertido + 30% Calinski-Harabasz), '
               f'o cualquiera de ellos de forma individual.'),
        bullet('Se ofrece una vista previa del gráfico de codo (elbow chart) antes de ejecutar '
               'la segmentación completa, permitiendo al usuario forzar manualmente un k concreto.'),
        sp(0.2),
        p('<b>Algoritmo DBSCAN:</b>', 'body'),
        bullet(f'{B("ε (Epsilon):")} radio de vecindad. Controla qué tan cerca deben estar '
               'dos puntos para considerarse vecinos.'),
        bullet(f'{B("min_samples:")} número mínimo de vecinos para que un punto sea núcleo. '
               'Los puntos sin suficientes vecinos se etiquetan como "Noise".'),
        bullet('DBSCAN encuentra clústeres de forma arbitraria y no requiere especificar k. '
               'Especialmente útil cuando los segmentos no son esféricos.'),
        sp(0.2),
        p('<b>Parámetros configurables:</b>', 'body'),
        bullet('Selección del algoritmo: K-Means o DBSCAN.'),
        bullet('Rango k_min / k_max (K-Means).'),
        bullet('Método de selección automática de k: combined, silhouette, davies_bouldin, elbow.'),
        bullet('Override manual de k tras ver el gráfico de codo.'),
        bullet('ε y min_samples (DBSCAN).'),
        sp(0.3),
    ]

    # ── 2.3 ABC ───────────────────────────────────────────────────────────────
    story += [
        p(B('2.3 Análisis ABC (Pareto)'), 'h2'),
        p('<b>Concepto:</b> Basado en el principio de Pareto (80/20), clasifica a los clientes '
          'en tres categorías según su contribución acumulada a los ingresos totales. Es el '
          'método más sencillo y rápido, ideal para una primera priorización.', 'body'),
        p('<b>Proceso:</b>', 'body'),
        bullet('Se calcula el gasto total por cliente (suma de order_total).'),
        bullet('Se ordenan los clientes de mayor a menor gasto.'),
        bullet('Se calcula el porcentaje acumulado de ingresos que representa cada cliente.'),
        bullet('Se asigna clase A a los primeros clientes que acumulan hasta el umbral_A, '
               'clase B a los siguientes hasta el umbral_B, y clase C al resto.'),
        sp(0.2),
        p('<b>Umbrales predeterminados:</b> A = 80%, B = 95% (es decir, B cubre el 80–95% '
          'acumulado y C el 95–100%).', 'body'),
        p('<b>Parámetros configurables:</b>', 'body'),
        bullet('Umbral A (slider 50%–90%): porcentaje de ingresos acumulado para la clase A.'),
        bullet('Umbral B (slider: umbral_A+1% a 99%): límite superior de la clase B.'),
        sp(0.3),
    ]

    # ── 2.4 LRFMS ─────────────────────────────────────────────────────────────
    story += [
        p(B('2.4 LRFMS — Segmentación por series temporales'), 'h2'),
        p('<b>Referencia académica:</b> Wang, S., Sun, L. & Yu, Y. (2024). '
          f'{I("Scientific Reports")}, 14, 17491. Este es el método más avanzado '
          'y experimental de los cuatro implementados.', 'body'),
        sp(0.2),
        p('<b>Concepto:</b> A diferencia de los métodos estáticos (RFM snapshot), LRFMS '
          'divide el historial de pedidos en N intervalos temporales iguales y calcula '
          'cinco métricas por cada (cliente, intervalo):', 'body'),
        bullet(f'{B("L (Length):")} amplitud del comportamiento del cliente en el intervalo. '
               'Medida como el número de días entre la primera y la última compra del intervalo.'),
        bullet(f'{B("R′ (Recency-prime):")} tiempo medio entre las últimas P transacciones '
               'y el final del intervalo. Captura la recencia reciente, no solo la última compra.'),
        bullet(f'{B("F (Frequency):")} número de pedidos únicos en el intervalo.'),
        bullet(f'{B("M (Monetary):")} gasto total en el intervalo.'),
        bullet(f'{B("S (Satisfaction):")} métrica de satisfacción por intervalo (ver más abajo).'),
        sp(0.2),
        p('Con este enfoque se construye una <b>matriz de series temporales</b> '
          '(clientes × intervalos × métricas). Esta matriz se normaliza y se clusteriza '
          'con K-Means para identificar patrones de evolución en el tiempo.', 'body'),
        sp(0.2),
        p(B('La métrica S (Satisfacción) — Implementación actual'), 'h3'),
        p('La implementación actual de S deriva la puntuación de satisfacción a partir de '
          'la <b>tasa de devoluciones por intervalo</b>. El fundamento es que un cliente '
          'que devuelve muchos artículos está, presumiblemente, insatisfecho. '
          'No se requieren datos de encuestas.', 'body'),
        sp(0.1),
    ]

    smap = [
        ['Tasa de devoluciones', 'Puntuación S', 'Interpretación'],
        ['0%',       '9.0', 'Perfecto — sin devoluciones'],
        ['1 – 2%',   '8.5', 'Excelente'],
        ['3 – 5%',   '7.5 – 8.0', 'Muy bueno'],
        ['6 – 10%',  '6.0 – 6.5', 'Bueno'],
        ['11 – 20%', '4.0', 'Problemas evidentes'],
        ['> 20%',    '2.0', 'Problemas graves'],
    ]
    t4 = Table(smap,
               colWidths=[4*cm, 3*cm, PAGE_W - 2*MARGIN - 7*cm],
               style=TableStyle([
                   ('BACKGROUND',    (0,0), (-1,0), PINK),
                   ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                   ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                   ('FONTSIZE',      (0,0), (-1,-1), 9),
                   ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor('#fdf0f6')]),
                   ('GRID',          (0,0), (-1,-1), 0.4, GRAY_BORDER),
                   ('TOPPADDING',    (0,0), (-1,-1), 5),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                   ('LEFTPADDING',   (0,0), (-1,-1), 10),
                   ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
               ]))
    story += [t4, sp(0.3)]

    story += [
        p('Para activar S basada en devoluciones, el usuario debe marcar la opción '
          '"Tratar filas con cantidad negativa como eventos de devolución" en el '
          f'{B("Paso 3 (Mapeo)")}. Al hacerlo:', 'body'),
        bullet('Las filas con cantidad negativa se preservan durante la limpieza (no se eliminan).'),
        bullet('El sistema genera dos DataFrames paralelos: uno de pedidos normales y otro '
               'que incluye los eventos de devolución.'),
        bullet('La opción "Eliminar valores negativos" en el Paso 4 queda desactivada visualmente.'),
        bullet('En el Paso 5, se muestra un banner verde confirmando que las devoluciones están activas.'),
        sp(0.2),
        p(B('Peso de S'), 'h3'),
        p('El parámetro <b>s_weight</b> controla la influencia de S en el clustering:', 'body'),
        bullet(f'{B("s_weight = 0")} — S queda completamente excluida. El clustering usa solo L, R′, F, M.'),
        bullet(f'{B("s_weight = 1.0")} — S tiene el mismo peso que las demás métricas.'),
        bullet(f'{B("s_weight > 1.0")} — S se amplifica, aumentando su influencia relativa.'),
        sp(0.2),
        p(B('Trabajo en curso — S desde encuestas'), 'h3'),
        info_box(
            '🔬 <b>Línea de investigación activa:</b> Se está trabajando en la implementación de S '
            'a partir del sistema propuesto en el paper original, donde la satisfacción se extrae '
            'de tres encuestas vinculadas a cada pedido: <b>pre-entrega</b> (expectativas antes del envío), '
            '<b>entrega</b> (experiencia en la recepción) y <b>post-entrega</b> (satisfacción tras el uso). '
            'Cuando el dataset incluya estas valoraciones mapeadas a la columna "satisfaction", '
            'el sistema calculará S como la media ponderada de las tres encuestas en lugar de '
            'derivarla de la tasa de devoluciones.',
            bg=HexColor('#fdf0f6'), border=PINK
        ),
        sp(0.3),
        p(B('Demás parámetros configurables de LRFMS:'), 'h3'),
        bullet(f'{B("n_intervals (2–12):")} número de intervalos temporales en que se divide '
               'el historial. Un valor mayor captura más granularidad pero requiere más datos por cliente.'),
        bullet(f'{B("p_value (1–10):")} número de transacciones recientes que se promedian '
               "para calcular R\u2032. Un p mayor suaviza la recencia."),
        bullet(f'{B("k_min / k_max:")} rango de número de clústeres a evaluar.'),
        bullet(f'{B("Método de selección de k:")} igual que en RFM K-Means '
               '(combined, silhouette, davies_bouldin, elbow).'),
        pb(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — VALORES NULOS
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        section_header('3', 'Tratamiento de valores nulos y decisiones de calidad de datos',
                       HexColor('#488f31')),
        sp(0.4),
        p('La calidad del dato es una etapa crítica antes de cualquier proceso de segmentación. '
          'Un cliente mal identificado o un pedido sin importe introduce ruido que distorsiona '
          'los resultados.', 'body'),
        sp(0.3),
        p(B('3.1 Reporte de calidad pre-limpieza'), 'h2'),
        p('Inmediatamente después de subir el archivo, el sistema genera un '
          '<b>informe de calidad</b> que se muestra en el Paso 4:', 'body'),
        bullet('Tabla con el número de valores nulos y valores negativos por columna.'),
        bullet('Número total de filas duplicadas.'),
        bullet('Indicadores visuales: fondo amarillo si el problema afecta entre 0 y 10% de '
               'las filas, fondo rojo si supera el 10%.'),
        sp(0.2),
        p(B('3.2 Opciones de limpieza'), 'h2'),
        p('El usuario puede activar o desactivar tres filtros de forma independiente:', 'body'),
        bullet(f'{B("Eliminar filas con valores nulos")} en columnas requeridas '
               '(customer_id, order_id, order_date, order_total).'),
        bullet(f'{B("Eliminar filas con valores numéricos negativos")} '
               '(order_total < 0). Se desactiva automáticamente si el usuario ha configurado '
               'filas negativas como eventos de devolución en LRFMS.'),
        bullet(f'{B("Eliminar filas duplicadas")} '
               '(misma combinación customer_id + order_id + order_date).'),
        sp(0.3),
        p(B('3.3 Decisión de diseño sobre customer_id nulo'), 'h2'),
        info_box(
            '📋 <b>Decisión de diseño:</b> Los valores nulos en la columna <b>customer_id</b> '
            'se eliminan siempre, independientemente de que el filtro "Eliminar nulos" esté '
            'activado o no. '
            'El razonamiento detrás de esta decisión es el siguiente: un customer_id nulo '
            'significa que no se puede identificar a quién pertenece ese pedido. '
            'Si se agruparan todos estos pedidos bajo un "cliente nulo", se estaría '
            'creando una entidad artificial que concentraría transacciones de múltiples '
            'clientes desconocidos, sesgando gravemente las métricas RFM de ese "cliente". '
            'Introducir este tipo de dato artificial en el modelo de segmentación produciría '
            'un segmento espurio sin ningún valor de negocio. Se prefiere perder esas filas '
            'a contaminar el análisis.',
            bg=HexColor('#f0f7f0'), border=HexColor('#2a7a3b')
        ),
        sp(0.3),
        p(B('3.4 Eliminación de order_total cero/negativo'), 'h2'),
        p('Además de los filtros opcionales, el sistema aplica siempre una regla fija: '
          'las filas cuyo <b>order_total ≤ 0</b> se eliminan del DataFrame de pedidos '
          'normales, ya que no aportan valor monetario y distorsionarían las métricas M y F. '
          'La única excepción es cuando el usuario activa el modo de devoluciones en LRFMS, '
          'caso en que las filas con order_total negativo se preservan en un DataFrame '
          'paralelo (<i>orders_with_returns_df</i>) exclusivamente para el cálculo de S.', 'body'),
        sp(0.3),
        p(B('3.5 Deduplicación'), 'h2'),
        p('La deduplicación se realiza sobre el DataFrame <b>crudo</b> (antes de cualquier '
          'transformación), lo que garantiza que el conteo de duplicados sea exacto y no '
          'esté afectado por el procesamiento previo de columnas. Una vez eliminados los '
          'duplicados, se aplica el resto de filtros sobre el conjunto ya limpio.', 'body'),
        pb(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4 — DASHBOARDS
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        section_header('4', 'Dashboards y visualizaciones por método', PURPLE),
        sp(0.4),
        p('Cada método de segmentación tiene un <b>dashboard diferente</b> diseñado para '
          'destacar la información más relevante de ese análisis concreto. El dashboard se '
          'abre como una capa modal sobre la página de resultados y utiliza '
          '<b>Recharts</b> para todas las visualizaciones.', 'body'),
        sp(0.3),
        p(B('Gráficos comunes a todos los métodos'), 'h2'),
        p('Los siguientes gráficos aparecen en todos los dashboards:', 'body'),
        bullet(f'{B("Gráfico de pastel")} — Distribución de clientes por segmento (%). '
               'Incluye etiqueta con nombre del segmento y porcentaje.'),
        bullet(f'{B("Gráfico de barras — Clientes por segmento")} — '
               'Número absoluto de clientes, ordenados de mayor a menor.'),
        bullet(f'{B("Gráfico de barras — % Clientes vs. % Ingresos")} — '
               'Comparación lado a lado de la cuota de clientes y la cuota de ingresos de cada segmento.'),
        bullet(f'{B("Top 10 clientes por segmento")} — '
               'Tabla con los 10 mayores clientes de cada segmento (seleccionable con botones), '
               'ordenados por valor monetario.'),
        sp(0.3),
        p(B('4.1 Dashboard RFM Quintiles — gráficos exclusivos'), 'h2'),
        bullet(f'{B("Perfil RFM medio normalizado (barras agrupadas)")} — '
               'Muestra la recencia, frecuencia y valor monetario promedio de cada segmento, '
               'normalizados entre 0 y 100% para hacer comparables las tres métricas. '
               'Permite identificar qué dimensión caracteriza a cada segmento.'),
        sp(0.3),
        p(B('4.2 Dashboard RFM K-Means — gráficos exclusivos'), 'h2'),
        bullet(f'{B("Gráfico de burbuja — Recencia vs. Monetario")} — '
               'Cada burbuja representa un segmento/clúster. El eje X es la recencia media, '
               'el eje Y el valor monetario medio, y el tamaño de la burbuja es proporcional '
               'al número de clientes. Revela el posicionamiento relativo de los clústeres '
               'en el espacio RFM.'),
        bullet(f'{B("Perfil RFM medio normalizado (barras agrupadas)")} — '
               'Igual que en Quintiles (ver arriba).'),
        bullet(f'{B("Tabla de perfil de clúster con renombrado")} — '
               'Permite renombrar los clústeres (p. ej., de "Cluster 0" a "High Value") '
               'y muestra las estadísticas completas por clúster: media, desviación típica, '
               'mínimo y máximo de R, F y M. El renombrado se refleja en el archivo CSV descargado.'),
        sp(0.3),
        p(B('4.3 Dashboard ABC Analysis — gráficos exclusivos'), 'h2'),
        bullet(f'{B("Curva de Pareto ABC (gráfico compuesto, ancho completo)")} — '
               'Es el gráfico central del dashboard ABC. Muestra la curva de ingresos acumulados '
               'frente al porcentaje de clientes ordenados por gasto descendente. '
               'Incluye áreas coloreadas para las zonas A (azul), B (naranja) y C (rosa), '
               'líneas de referencia verticales en los umbrales A y B, y líneas horizontales '
               'en los porcentajes de ingresos correspondientes.'),
        sp(0.3),
        p(B('4.4 Dashboard LRFMS — gráficos exclusivos'), 'h2'),
        bullet(f'{B("Tabla de perfil de clúster LRFMS con renombrado")} — '
               'Igual que en K-Means pero con las métricas propias de LRFMS: '
               "R′ (recencia-prime), Frecuencia y Monetario. Las etiquetas se adaptan "
               'automáticamente al método.'),
        sp(0.3),
        info_box(
            '💡 <b>Nota sobre el renombrado de clústeres:</b> En los métodos K-Means y LRFMS, '
            'los clústeres se generan con nombres genéricos ("Cluster 0", "Cluster 1"...). '
            'La sección de perfil del dashboard permite al usuario asignarles nombres '
            'de negocio significativos. Al pulsar "Guardar nombres", el sistema actualiza '
            'tanto la vista del dashboard como el archivo CSV que se puede descargar.'
        ),
        pb(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5 — BIGQUERY Y HOJA DE RUTA CLOUD
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        section_header('5', 'Integración con Google BigQuery y hoja de ruta cloud',
                       HexColor('#003f5c')),
        sp(0.4),
        p('La plataforma ofrece actualmente dos vías de entrada de datos. La primera, '
          'carga de archivos locales (CSV/Excel). La segunda, consulta directa a '
          '<b>Google BigQuery</b>, lo que permite trabajar con datasets de cualquier '
          'tamaño sin necesidad de exportar ficheros.', 'body'),
        sp(0.3),
        p(B('5.1 Implementación actual de la entrada desde BigQuery'), 'h2'),
        p('<b>Mecanismo de autenticación:</b>', 'body'),
        p('La autenticación se realiza mediante una <b>cuenta de servicio de Google Cloud</b>. '
          'El usuario sube el archivo JSON de la clave de la cuenta de servicio directamente '
          'en la interfaz (mediante drag & drop o selector de archivos). '
          'Alternativamente, puede pegar el contenido JSON manualmente.', 'body'),
        p('La cuenta de servicio debe tener asignados los roles:', 'body'),
        bullet(f'{B("BigQuery Data Viewer")} — para leer datos de las tablas.'),
        bullet(f'{B("BigQuery Job User")} — para crear y ejecutar jobs de consulta. '
               '<b>Este rol es imprescindible</b> ya que BigQuery procesa las consultas '
               'como jobs asíncronos incluso para SELECT simples; sin él se produce un '
               'error 403 de scope insuficiente.'),
        sp(0.2),
        p('<b>Flujo técnico:</b>', 'body'),
        bullet('El JSON de la clave se envía al backend vía POST /upload/bigquery.'),
        bullet(f'El servicio {MONO("bigquery_connector.py")} valida el JSON (campos obligatorios: '
               f'{MONO("type")}, {MONO("project_id")}, {MONO("private_key")}, {MONO("client_email")}).'),
        bullet('Se construyen las credenciales con el scope '
               f'{MONO("https://www.googleapis.com/auth/bigquery")} (scope completo, no readonly).'),
        bullet('Se ejecuta la consulta SQL y el resultado se convierte en un DataFrame de pandas.'),
        bullet('A partir de ahí, el flujo es idéntico al de un archivo subido localmente.'),
        sp(0.2),
        p('<b>Importaciones opcionales (lazy imports):</b>', 'body'),
        p(f'El módulo {MONO("google-cloud-bigquery")} se importa dentro de un bloque '
          f'{MONO("try/except")} al arrancar el backend. Si el paquete no está instalado, '
          'el conector devuelve un error 501 (Not Implemented) en lugar de impedir el '
          'arranque del servidor. El script de inicio ({MONO("start.sh")}) instala '
          'automáticamente todas las dependencias del {MONO("requirements.txt")} '
          'antes de arrancar el servidor.', 'body'),
        sp(0.3),
        p(B('5.2 Hoja de ruta — Trabajo en curso'), 'h2'),
        info_box(
            '🚧 <b>Funcionalidades en desarrollo activo:</b>\n\n'
            '• <b>Escritura de resultados en BigQuery:</b> Una vez completada la segmentación, '
            'poder escribir directamente los resultados (customer_id + segmento + métricas) '
            'en una tabla de BigQuery destino, eliminando la necesidad de descargar y '
            're-subir el CSV a otros sistemas.\n\n'
            '• <b>Ejecución en Google Cloud:</b> El objetivo es mover todos los procesos '
            'que actualmente se ejecutan en local —especialmente los algoritmos de clustering '
            'y la agregación RFM de grandes volúmenes— a infraestructura de Google Cloud. '
            'Las opciones evaluadas incluyen Cloud Run (contenedores serverless), '
            'Cloud Functions (ejecución de funciones individuales) y Vertex AI '
            '(para los pasos de ML más intensivos como K-Means y LRFMS). '
            'Esto permitiría procesar datasets de millones de clientes sin limitaciones '
            'de memoria local.\n\n'
            '• <b>Orquestación de pipelines:</b> Integración con Cloud Composer (Apache Airflow) '
            'para programar ejecuciones periódicas automáticas de la segmentación '
            '(p. ej., mensual) sobre datos frescos de BigQuery.',
            bg=HexColor('#e8f4fd'), border=HexColor('#003f5c')
        ),
        sp(0.4),
        p(B('5.3 Arquitectura objetivo (cloud-native)'), 'h2'),
    ]

    arch = [
        ['Componente actual', '→', 'Equivalente cloud'],
        ['Servidor Uvicorn local (FastAPI)', '→', 'Cloud Run (contenedor Docker)'],
        ['Archivos CSV en disco local', '→', 'Cloud Storage (GCS)'],
        ['Sesiones en memoria (dict)', '→', 'Cloud Memorystore (Redis)'],
        ['Clustering local (scikit-learn)', '→', 'Vertex AI Training Jobs'],
        ['Resultados en CSV descargable', '→', 'Escritura directa en BigQuery'],
        ['Ejecución manual', '→', 'Cloud Scheduler + Cloud Composer'],
    ]
    t5 = Table(arch,
               colWidths=[5.5*cm, 1*cm, PAGE_W - 2*MARGIN - 6.5*cm],
               style=TableStyle([
                   ('BACKGROUND',    (0,0), (-1,0), HexColor('#003f5c')),
                   ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                   ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                   ('FONTSIZE',      (0,0), (-1,-1), 9),
                   ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor('#e8f4fd')]),
                   ('GRID',          (0,0), (-1,-1), 0.4, GRAY_BORDER),
                   ('TOPPADDING',    (0,0), (-1,-1), 6),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                   ('LEFTPADDING',   (0,0), (-1,-1), 10),
                   ('ALIGN',         (1,0), (1,-1), 'CENTER'),
                   ('TEXTCOLOR',     (1,1), (1,-1), HexColor('#003f5c')),
                   ('FONTNAME',      (1,1), (1,-1), 'Helvetica-Bold'),
                   ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
               ]))
    story += [t5, sp(0.5)]

    # ── Cierre ─────────────────────────────────────────────────────────────────
    story += [
        hr(ACCENT_SOFT),
        sp(0.3),
        p(I('Documento generado automáticamente a partir del código fuente del repositorio. '
            'Para información actualizada consultar el propio código en product/.'), 'note'),
    ]

    doc.build(story)
    print(f'PDF generado: {out}')


if __name__ == '__main__':
    build()
