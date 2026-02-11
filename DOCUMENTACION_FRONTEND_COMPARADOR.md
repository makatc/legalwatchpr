# Documentación del Frontend - Comparador de Versiones Legales

## Descripción General

El **Comparador de Enmiendas** es una aplicación web que permite comparar diferentes versiones de proyectos de ley (bills) de Puerto Rico, mostrando las diferencias textuales entre documentos y proporcionando análisis asistido por IA.

---

## Arquitectura del Frontend

### Stack Tecnológico
- **Framework CSS**: Tailwind CSS (vía CDN)
- **Iconos**: Font Awesome 6.0.0
- **Fuentes**: Google Fonts (Inter)
- **Backend**: Django Templates
- **Estilo visual**: Diseño moderno con tema oscuro en sidebar

### Estructura de Archivos
```
core/templates/core/
├── base.html                    # Template base con sidebar y navegación
├── comparador_selector.html     # Página inicial: lista de proyectos de ley
└── comparador.html              # Página de comparación de versiones
```

---

## Flujo de Usuario

### 1. Página Principal del Comparador (`comparador_selector.html`)

**URL**: `/comparador/`

**Descripción**: Muestra una lista de todos los proyectos de ley disponibles para comparar.

#### Elementos Visuales:
- **Encabezado**: 
  - Título: "Comparador de Enmiendas"
  - Subtítulo: "Selecciona un Proyecto de Ley para analizar sus cambios"
  
- **Lista de Proyectos** (tarjetas interactivas):
  - Número del proyecto (ej: "P. de la C. 1001")
  - Estado del proyecto (badge con estado)
  - Título del proyecto
  - Fecha de última actualización
  - Indicador visual de navegación (flecha →)
  
- **Comportamiento**:
  - Hover: Fondo cambia a azul claro (`bg-blue-50`)
  - Click: Redirige a la página de comparación del proyecto específico

#### Diseño Visual:
```
┌─────────────────────────────────────────────┐
│   Comparador de Enmiendas                   │
│   Selecciona un Proyecto de Ley             │
├─────────────────────────────────────────────┤
│  ┌───────────────────────────────────────┐  │
│  │ P. de la C. 1001  [Activo]         → │  │
│  │ Título del proyecto...                │  │
│  │ Actualizado: 15 Ene 2026              │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ P. de la C. 1002  [En trámite]     → │  │
│  │ Título del proyecto...                │  │
│  │ Actualizado: 10 Feb 2026              │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

### 2. Página de Comparación (`comparador.html`)

**URL**: `/comparador/<bill_id>/`

**Descripción**: Interfaz completa para comparar versiones de un proyecto de ley específico.

#### Secciones Principales:

##### A. Encabezado del Proyecto
- Botón de retorno a la lista
- Número del proyecto (grande y destacado)
- Título del proyecto (truncado a 100 caracteres)
- Fecha de última actualización

##### B. Panel de Selección de Documentos (Grid 2/3)

**Elementos del Formulario**:

1. **Selector "Original"** (izquierda):
   - Fondo gris (`bg-gray-50`)
   - Dropdown con todas las versiones disponibles
   - Formato: 📅 DD/MM/AAAA - Nombre de la versión

2. **Flecha de dirección** (centro):
   - Icono `→` visual que indica la dirección de comparación

3. **Selector "Enmiendas"** (derecha):
   - Fondo azul claro (`bg-blue-50`)
   - Dropdown con versiones en orden inverso
   - Mismo formato de fecha

4. **Botones de Acción** (2 opciones):
   - **"Ver Diferencias"** (gris oscuro):
     - Icono: intercambio (`fa-exchange-alt`)
     - Muestra diff textual estándar
   
   - **"Explicar Cambios (IA)"** (púrpura):
     - Icono: robot (`fa-robot`)
     - Activa análisis de IA además del diff

##### C. Panel de Carga de Archivos (Grid 1/3)

**Funcionalidad**: Subir nuevas versiones del documento

- **Formatos soportados**: PDF (.pdf) y Word (.docx)
- **Campos**:
  - Input de texto: Nombre de la versión (ej: "Borrador en Word")
  - File input: Selector de archivo
  - Botón: "Añadir Versión" (azul claro)

##### D. Resultados de Comparación (condicional)

Aparece solo cuando se han seleccionado dos versiones:

1. **Comparativa Textual** (caja gris oscura):
   - Encabezado oscuro con leyenda de colores:
     - ❌ Rojo: Texto eliminado
     - ✅ Verde: Texto añadido
   - Contenido:
     - Tabla diff estilo HTML
     - Números de línea en gris
     - Texto en fuente monoespaciada (Courier New)
     - Fondo amarillo para cambios (`diff_chg`)

2. **Resumen Jurídico (IA)** (caja púrpura):
   - Solo aparece si se activó el análisis IA
   - Encabezado púrpura con icono de cerebro
   - Contenido en prosa con formato tipográfico
   - Fondo: `bg-purple-50`

---

## Diseño Visual Detallado

### Paleta de Colores

| Elemento | Color | Código Tailwind |
|----------|-------|-----------------|
| Fondo general | Gris muy claro | `bg-gray-50` |
| Tarjetas | Blanco | `bg-white` |
| Sidebar | Gris oscuro | `bg-slate-900` |
| Primario (Original) | Gris | `bg-gray-50` / `border-gray-300` |
| Secundario (Enmiendas) | Azul | `bg-blue-50` / `border-blue-300` |
| IA | Púrpura | `bg-purple-600` |
| Diff - Añadido | Verde claro | `bg-green-100` / `text-green-700` |
| Diff - Eliminado | Rojo claro | `bg-red-100` / `text-red-700` |
| Diff - Modificado | Amarillo | `bg-yellow-100` / `text-yellow-700` |

### Tipografía
- **Familia principal**: Inter (Google Fonts)
- **Diff/Código**: Courier New (monospace)
- **Tamaños**:
  - Título principal: `text-3xl` (30px)
  - Subtítulos: `text-2xl` (24px)
  - Texto normal: `text-sm` / `text-base`
  - Labels: `text-xs` (uppercase, bold)

---

## Estilos CSS Personalizados

### Tabla Diff

```css
.diff-container table {
    width: 100%;
    border-collapse: collapse;
}

.diff-container td {
    padding: 8px 10px;
    vertical-align: top;
    font-family: 'Courier New', monospace;
    font-size: 13px;
}

.diff_header {
    background-color: #f9fafb;  /* Números de línea */
    color: #9ca3af;
    text-align: right;
    border-right: 1px solid #e5e7eb;
}

.diff_add {
    background-color: #dcfce7;   /* Verde: texto añadido */
    color: #15803d;
}

.diff_chg {
    background-color: #fef9c3;   /* Amarillo: texto modificado */
    color: #a16207;
}

.diff_sub {
    background-color: #fee2e2;   /* Rojo: texto eliminado */
    color: #b91c1c;
    text-decoration: line-through;
}
```

---

## Modelo de Datos

### Bill (Proyecto de Ley)
```python
- number: CharField (único, ej: "P. de la C. 1001")
- title: TextField
- last_updated: DateTimeField (auto)
- ai_score: IntegerField
- ai_analysis: TextField
- relevance_why: CharField
```

### BillVersion (Versión de Documento)
```python
- bill: ForeignKey(Bill)
- version_name: CharField (ej: "Entirillado", "Aprobado")
- pdf_file: FileField (upload_to='bills_pdfs/')
- full_text: TextField (extraído automáticamente)
- created_at: DateTimeField (auto)
```

---

## Interacciones y Comportamiento

### Estados Interactivos

1. **Hover en tarjetas de proyectos**:
   - Fondo cambia a `bg-blue-50`
   - Botón de flecha cambia de azul claro a azul oscuro

2. **Hover en botones**:
   - "Ver Diferencias": `hover:bg-gray-900`
   - "Explicar Cambios (IA)": `hover:bg-purple-700`
   - "Añadir Versión": `hover:bg-blue-200`

3. **Focus en selectores**:
   - Borde resaltado con `focus:ring-2`
   - Color del anillo según el tipo (gris para Original, azul para Enmiendas)

### Validaciones

- Ambos selectores deben tener una versión seleccionada antes de comparar
- El archivo subido debe ser .pdf o .docx
- El nombre de versión es requerido al subir archivo

---

## Navegación (Sidebar)

El sidebar es consistente en toda la aplicación:

```
┌────────────────────┐
│ ⚖️ LegalWatchAI    │  ← Logo
├────────────────────┤
│ PRINCIPAL          │
│ 📊 Dashboard       │
│ 📰 Noticias        │
│ 📅 Agenda          │
│ 🔄 Comparador      │  ← Activo
├────────────────────┤
│ HERRAMIENTAS       │
│ 🛡️ Administración  │
├────────────────────┤
│ 🚪 Cerrar Sesión   │
└────────────────────┘
```

- Fondo: `bg-slate-900` (gris muy oscuro)
- Elemento activo: `bg-blue-900` con texto `text-blue-200`
- Ancho fijo: `w-64` (256px)

---

## Características Técnicas

### Responsive Design
- Grid adaptativo: `grid-cols-1 lg:grid-cols-3`
- Breakpoints de Tailwind:
  - `md:` (tablet) - 768px
  - `lg:` (desktop) - 1024px

### Accesibilidad
- Etiquetas semánticas (`<label>`, `<button>`, `<nav>`)
- Iconos descriptivos con Font Awesome
- Contraste adecuado en todos los elementos

### Optimizaciones
- CDN para Tailwind y Font Awesome (carga rápida)
- Fuentes optimizadas de Google Fonts
- Renderizado condicional (`{% if %}`) para mostrar resultados

---

## Ejemplo de Flujo Completo

1. Usuario accede a `/comparador/`
2. Ve lista de proyectos de ley
3. Hace click en "P. de la C. 1001"
4. Llega a `/comparador/1/`
5. Selecciona versión original del dropdown izquierdo (ej: "Radicación - 01/01/2026")
6. Selecciona versión con enmiendas del dropdown derecho (ej: "Entirillado - 15/01/2026")
7. Click en "Ver Diferencias"
8. La página recarga y muestra:
   - Tabla diff con cambios resaltados en colores
   - Números de línea para referencia
9. (Opcional) Click en "Explicar Cambios (IA)"
10. Se añade una sección con resumen jurídico generado por IA

---

## Ventajas del Diseño

✅ **Intuitivo**: Flujo visual claro con flechas y colores diferenciados  
✅ **Moderno**: Uso de Tailwind con efectos de transición suaves  
✅ **Funcional**: Dos modos de análisis (diff manual + IA)  
✅ **Flexible**: Permite subir nuevas versiones directamente  
✅ **Accesible**: Sidebar siempre visible con navegación clara  

---

## Posibles Mejoras Futuras

- [ ] Comparación de más de 2 versiones simultáneas
- [ ] Exportar comparación a PDF
- [ ] Resaltar cambios críticos (IA identifica secciones importantes)
- [ ] Historial de comparaciones recientes
- [ ] Comentarios en línea sobre cambios específicos
- [ ] Modo oscuro completo (dark mode)
- [ ] Búsqueda dentro del diff
- [ ] Integración con sistemas legislativos oficiales

---

## Conclusión

El frontend del Comparador de Enmiendas es una interfaz limpia y profesional que combina tecnologías modernas (Tailwind CSS) con funcionalidad práctica (diff visual + análisis IA). Su diseño prioriza la usabilidad y claridad visual, facilitando la tarea compleja de comparar documentos legales extensos.
