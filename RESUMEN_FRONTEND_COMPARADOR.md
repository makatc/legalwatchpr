# Resumen: Frontend del Comparador de Versiones Legales

## 📋 Descripción Breve

El **Comparador de Enmiendas** es una aplicación web Django que permite comparar diferentes versiones de proyectos de ley de Puerto Rico, mostrando diferencias textuales detalladas y análisis asistidos por IA.

---

## 🎯 Función Principal

Facilitar el análisis de cambios entre versiones de documentos legislativos mediante:
1. **Visualización diff** - Comparación textual lado a lado con colores
2. **Análisis IA** - Resumen jurídico de los cambios principales
3. **Gestión de versiones** - Subida y almacenamiento de múltiples versiones

---

## 🖥️ Capturas Conceptuales del Frontend

### Pantalla 1: Lista de Proyectos
- Selector inicial donde se muestran todos los proyectos de ley disponibles
- Cada tarjeta muestra: número, título, estado y última actualización
- Click en cualquier proyecto para acceder a sus versiones

### Pantalla 2: Comparador de Versiones
- **Panel izquierdo**: Selector de versión "Original"
- **Panel derecho**: Selector de versión "Enmiendas"
- **Panel lateral**: Carga de nuevos archivos PDF/DOCX
- **Botones de acción**: "Ver Diferencias" y "Explicar Cambios (IA)"

### Pantalla 3: Resultados
- **Tabla diff**: Comparación línea por línea con colores
  - 🔴 Rojo tachado = Texto eliminado
  - 🟢 Verde = Texto añadido
  - 🟡 Amarillo = Texto modificado
- **Análisis IA** (opcional): Resumen en prosa de cambios significativos

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Frontend** | Django Templates + Tailwind CSS |
| **Backend** | Django (Python) |
| **Base de datos** | PostgreSQL + pgvector |
| **Iconos** | Font Awesome 6.0 |
| **Tipografía** | Google Fonts (Inter) |

---

## 📁 Archivos Clave del Frontend

```
core/templates/core/
├── base.html                      # Layout base con sidebar
├── comparador_selector.html       # Lista de proyectos (/comparador/)
└── comparador.html                # Comparación de versiones (/comparador/<id>/)

core/
├── models.py                      # Bill y BillVersion
├── views.py                       # Lógica de comparador
└── urls.py                        # Rutas
```

---

## 🎨 Características de Diseño

### Visual
- **Sidebar fijo** con navegación principal (gris oscuro - slate-900)
- **Tarjetas blancas** sobre fondo gris claro (gray-50)
- **Código de colores** intuitivo para diferenciar Original vs Enmiendas
- **Tipografía moderna** (Inter) con monospace para código (Courier New)

### Interacción
- **Hover states** en todos los elementos interactivos
- **Transiciones suaves** (150-300ms)
- **Responsive design** (mobile, tablet, desktop)
- **Feedback visual** inmediato en acciones

### Accesibilidad
- Contraste adecuado (WCAG)
- Etiquetas semánticas
- Iconos descriptivos

---

## 🔄 Flujo de Usuario Típico

```
1. Usuario accede a /comparador/
          ↓
2. Ve lista de proyectos de ley
          ↓
3. Click en proyecto (ej: "P. de la C. 1001")
          ↓
4. Selecciona versión Original (dropdown izquierdo)
          ↓
5. Selecciona versión Enmiendas (dropdown derecho)
          ↓
6. Click en "Ver Diferencias" o "Explicar Cambios (IA)"
          ↓
7. Visualiza resultados:
   - Tabla diff con cambios resaltados
   - (Opcional) Resumen jurídico IA
```

---

## 📊 Modelos de Datos

### Bill (Proyecto de Ley)
```python
- number: "P. de la C. 1001" (único)
- title: Título completo
- last_updated: Auto-actualizado
- ai_score: Puntuación IA
- ai_analysis: Análisis previo
```

### BillVersion (Versión)
```python
- bill: Relación con Bill
- version_name: "Radicación", "Entirillado", etc.
- pdf_file: Archivo cargado
- full_text: Texto extraído automáticamente
- created_at: Timestamp
```

---

## 🎨 Paleta de Colores

| Uso | Color | Hex |
|-----|-------|-----|
| Sidebar | Slate 900 | #1e293b |
| Fondo | Gray 50 | #f9fafb |
| Original | Gray 50 | #f9fafb |
| Enmiendas | Blue 50 | #eff6ff |
| Diff + | Green 100 | #dcfce7 |
| Diff - | Red 100 | #fee2e2 |
| Diff ~ | Yellow 100 | #fef9c3 |
| IA | Purple 600 | #9333ea |

---

## 📖 Documentación Completa

Para información detallada, consulta:

1. **[DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md)**
   - Descripción exhaustiva de componentes
   - Guía de estilos CSS
   - Características técnicas completas

2. **[DIAGRAMA_VISUAL_COMPARADOR.md](./DIAGRAMA_VISUAL_COMPARADOR.md)**
   - Diagramas ASCII de layouts
   - Flujo de interacción detallado
   - Mockups de pantallas

---

## 🚀 Ventajas del Sistema

✅ **Intuitivo** - Interfaz clara con código de colores  
✅ **Completo** - Diff manual + análisis IA  
✅ **Flexible** - Permite subir nuevas versiones  
✅ **Moderno** - Diseño actualizado con Tailwind  
✅ **Funcional** - Enfocado en usabilidad práctica  

---

## 🔮 Posibles Mejoras Futuras

- Comparación de 3+ versiones simultáneas
- Exportar comparación a PDF
- Comentarios inline en cambios
- Modo oscuro completo
- Búsqueda dentro del diff
- Notificaciones de nuevas versiones

---

## 📝 Conclusión

El frontend del Comparador de Enmiendas representa una solución moderna y práctica para un problema complejo: **analizar cambios en documentos legales extensos**. 

Combina tecnologías probadas (Django, Tailwind) con funcionalidades innovadoras (análisis IA) para crear una experiencia de usuario superior que facilita el trabajo de abogados, legisladores y ciudadanos interesados en el proceso legislativo de Puerto Rico.

---

**Última actualización**: Febrero 2026  
**Versión**: 1.0  
**Proyecto**: LegalWatch AI - Puerto Rico
