# 📚 Índice - Documentación del Comparador de Versiones Legales

## Bienvenido a la Documentación del Frontend

Esta documentación describe en detalle el **Comparador de Enmiendas**, la interfaz web que permite comparar diferentes versiones de proyectos de ley de Puerto Rico.

---

## 📖 Documentos Disponibles

### 1️⃣ [RESUMEN_FRONTEND_COMPARADOR.md](./RESUMEN_FRONTEND_COMPARADOR.md)
**📄 Resumen Ejecutivo**

- Descripción breve y concisa
- Stack tecnológico utilizado
- Flujo de usuario típico
- Paleta de colores
- Ventajas del sistema

**👉 Recomendado para**: Stakeholders, product managers, overview rápido

**⏱️ Tiempo de lectura**: 5 minutos

---

### 2️⃣ [DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md)
**📘 Documentación Técnica Completa**

- Arquitectura detallada del frontend
- Descripción exhaustiva de cada página
- Componentes visuales y su comportamiento
- Estilos CSS personalizados
- Modelo de datos (Bill, BillVersion)
- Características técnicas
- Guía de navegación

**👉 Recomendado para**: Desarrolladores, diseñadores, arquitectos de software

**⏱️ Tiempo de lectura**: 20-30 minutos

---

### 3️⃣ [DIAGRAMA_VISUAL_COMPARADOR.md](./DIAGRAMA_VISUAL_COMPARADOR.md)
**🎨 Diagramas Visuales y Mockups**

- Diagramas ASCII de layouts
- Mockups de pantallas principales
- Componentes visuales en detalle
- Flujo de interacción completo
- Paleta de colores visual
- Responsividad y breakpoints
- Iconografía utilizada

**👉 Recomendado para**: Diseñadores UX/UI, desarrolladores frontend

**⏱️ Tiempo de lectura**: 15-20 minutos

---

## 🗺️ Guía de Navegación por Rol

### 👔 Si eres un Stakeholder o Manager
1. Lee primero: **RESUMEN_FRONTEND_COMPARADOR.md**
2. Opcional: **DIAGRAMA_VISUAL_COMPARADOR.md** (para ver mockups)

### 💻 Si eres un Desarrollador
1. Comienza con: **RESUMEN_FRONTEND_COMPARADOR.md** (context)
2. Continúa con: **DOCUMENTACION_FRONTEND_COMPARADOR.md** (detalles técnicos)
3. Consulta: **DIAGRAMA_VISUAL_COMPARADOR.md** (cuando necesites referencia visual)

### 🎨 Si eres un Diseñador UX/UI
1. Empieza con: **DIAGRAMA_VISUAL_COMPARADOR.md** (mockups y paleta)
2. Profundiza en: **DOCUMENTACION_FRONTEND_COMPARADOR.md** (interacciones y estilos)
3. Contexto general: **RESUMEN_FRONTEND_COMPARADOR.md**

### 🔍 Si eres un Auditor o QA
1. Lee: **DOCUMENTACION_FRONTEND_COMPARADOR.md** (flujos completos)
2. Referencia: **DIAGRAMA_VISUAL_COMPARADOR.md** (estados esperados)

---

## 🎯 Respuestas Rápidas

### ¿Qué tecnologías usa el frontend?
- Django Templates
- Tailwind CSS (CDN)
- Font Awesome 6.0
- Google Fonts (Inter)

→ Ver: [RESUMEN_FRONTEND_COMPARADOR.md](./RESUMEN_FRONTEND_COMPARADOR.md#-stack-tecnológico)

### ¿Cómo funciona el flujo de usuario?
1. Lista de proyectos → 2. Selección de versiones → 3. Visualización de diferencias

→ Ver: [DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md#flujo-de-usuario)

### ¿Qué archivos HTML necesito modificar?
- `comparador_selector.html` - Lista de proyectos
- `comparador.html` - Comparación de versiones
- `base.html` - Layout general

→ Ver: [DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md#estructura-de-archivos)

### ¿Cuáles son los colores principales?
- Original: Gray-50 (#f9fafb)
- Enmiendas: Blue-50 (#eff6ff)
- Diff +: Green-100 (#dcfce7)
- Diff -: Red-100 (#fee2e2)
- IA: Purple-600 (#9333ea)

→ Ver: [DIAGRAMA_VISUAL_COMPARADOR.md](./DIAGRAMA_VISUAL_COMPARADOR.md#paleta-de-colores-visual)

### ¿Cómo se almacenan las versiones?
Modelo `BillVersion`:
- Archivo PDF/DOCX cargado
- Texto extraído automáticamente
- Nombre de versión personalizable

→ Ver: [DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md#modelo-de-datos)

### ¿Cómo funciona el análisis IA?
Al hacer click en "Explicar Cambios (IA)", se envía un parámetro adicional (`ai=true`) que activa el análisis y muestra un resumen jurídico adicional.

→ Ver: [DOCUMENTACION_FRONTEND_COMPARADOR.md](./DOCUMENTACION_FRONTEND_COMPARADOR.md#d-resultados-de-comparación-condicional)

---

## 📂 Estructura del Proyecto

```
legalwatchpr/
├── core/
│   ├── templates/core/
│   │   ├── base.html                      # Layout principal
│   │   ├── comparador_selector.html       # Lista de proyectos
│   │   └── comparador.html                # Comparación
│   ├── models.py                          # Bill, BillVersion
│   ├── views.py                           # Lógica de comparador
│   └── urls.py                            # Rutas
├── RESUMEN_FRONTEND_COMPARADOR.md         # 📄 Resumen ejecutivo
├── DOCUMENTACION_FRONTEND_COMPARADOR.md   # 📘 Docs técnicas
├── DIAGRAMA_VISUAL_COMPARADOR.md          # 🎨 Mockups visuales
└── INDICE_COMPARADOR.md                   # 📚 Este archivo
```

---

## 🔗 Enlaces Rápidos

| Documento | Sección Destacada | Link |
|-----------|-------------------|------|
| Resumen | Stack Tecnológico | [Ver →](./RESUMEN_FRONTEND_COMPARADOR.md#-stack-tecnológico) |
| Resumen | Flujo de Usuario | [Ver →](./RESUMEN_FRONTEND_COMPARADOR.md#-flujo-de-usuario-típico) |
| Documentación | Página de Comparación | [Ver →](./DOCUMENTACION_FRONTEND_COMPARADOR.md#2-página-de-comparación-comparadorhtml) |
| Documentación | Estilos CSS | [Ver →](./DOCUMENTACION_FRONTEND_COMPARADOR.md#estilos-css-personalizados) |
| Documentación | Modelo de Datos | [Ver →](./DOCUMENTACION_FRONTEND_COMPARADOR.md#modelo-de-datos) |
| Diagramas | Layout Desktop | [Ver →](./DIAGRAMA_VISUAL_COMPARADOR.md#página-2-comparación-de-versiones-comparadorid) |
| Diagramas | Flujo de Interacción | [Ver →](./DIAGRAMA_VISUAL_COMPARADOR.md#flujo-de-interacción) |
| Diagramas | Paleta de Colores | [Ver →](./DIAGRAMA_VISUAL_COMPARADOR.md#paleta-de-colores-visual) |

---

## 💡 Consejos de Uso

### Para lectura lineal:
1. **RESUMEN_FRONTEND_COMPARADOR.md** (contexto general)
2. **DOCUMENTACION_FRONTEND_COMPARADOR.md** (detalles técnicos)
3. **DIAGRAMA_VISUAL_COMPARADOR.md** (referencia visual)

### Para consulta rápida:
- Usa el buscador de tu editor (Ctrl+F / Cmd+F)
- Navega por los encabezados (#, ##, ###)
- Consulta la tabla de "Respuestas Rápidas" arriba

### Para desarrollo:
1. Abre **DIAGRAMA_VISUAL_COMPARADOR.md** en una ventana
2. Trabaja con el código en otra
3. Consulta **DOCUMENTACION_FRONTEND_COMPARADOR.md** según necesites

---

## 🎓 Aprende Más

### Tecnologías Relacionadas
- [Tailwind CSS](https://tailwindcss.com/docs) - Framework CSS utilizado
- [Font Awesome](https://fontawesome.com/icons) - Biblioteca de iconos
- [Django Templates](https://docs.djangoproject.com/en/stable/topics/templates/) - Sistema de templates

### Conceptos Clave
- **Diff Algorithm**: Comparación de texto línea por línea
- **Hybrid Search**: Búsqueda combinando vectores y SQL (proyecto general)
- **Bill Versioning**: Sistema de versionado de documentos legislativos

---

## 📞 Contacto y Contribuciones

Si encuentras errores, tienes sugerencias o quieres contribuir a esta documentación:

1. Abre un issue en GitHub
2. Contacta al equipo de desarrollo
3. Envía un pull request con mejoras

---

## 📅 Última Actualización

**Fecha**: Febrero 11, 2026  
**Versión**: 1.0  
**Proyecto**: LegalWatch AI - Puerto Rico  
**Autor**: Documentación generada para el repositorio `makatc/legalwatchpr`

---

## ✅ Checklist de Documentación

- [x] Descripción general del sistema
- [x] Arquitectura del frontend
- [x] Flujos de usuario detallados
- [x] Componentes visuales
- [x] Estilos y diseño
- [x] Diagramas y mockups
- [x] Paleta de colores
- [x] Modelo de datos
- [x] Guía de navegación
- [x] Enlaces rápidos
- [x] FAQs y respuestas rápidas

---

**¡Comienza tu lectura con cualquiera de los tres documentos según tu necesidad!** 🚀
