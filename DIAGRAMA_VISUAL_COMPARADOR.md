# Diagrama Visual - Comparador de Versiones Legales

## Página 1: Selector de Proyectos (`/comparador/`)

```
┌─────────────┬───────────────────────────────────────────────────────────────────┐
│             │                                                                   │
│  LegalWatch │   Comparador de Enmiendas                                        │
│     AI      │   Selecciona un Proyecto de Ley para analizar sus cambios        │
│             │                                                                   │
│  📊Dashboard│   ┌───────────────────────────────────────────────────────────┐  │
│  📰Noticias │   │  P. de la C. 1001        [Activo]                    →   │  │
│  📅Agenda   │   │  Ley para establecer...                                   │  │
│  🔄Comparad→│   │  Actualizado: 15 Ene 2026                                 │  │
│             │   └───────────────────────────────────────────────────────────┘  │
│  🛡️Admin    │   ┌───────────────────────────────────────────────────────────┐  │
│             │   │  P. de la C. 1002        [En trámite]                →   │  │
│  🚪Logout   │   │  Proyecto para modificar el código penal...               │  │
│             │   │  Actualizado: 10 Feb 2026                                 │  │
└─────────────┤   └───────────────────────────────────────────────────────────┘  │
              │                                                                   │
              │   ← Volver al Dashboard                                          │
              │                                                                   │
              └───────────────────────────────────────────────────────────────────┘
```

---

## Página 2: Comparación de Versiones (`/comparador/<id>/`)

```
┌─────────────┬───────────────────────────────────────────────────────────────────┐
│             │  ← Volver a la lista                                             │
│  LegalWatch │  P. de la C. 1001                    Última actualización:       │
│     AI      │  Ley para establecer...                    15 Ene 2026          │
│             │                                                                   │
│  📊Dashboard│  ┌──────────────────────────────────────┬──────────────────────┐ │
│  📰Noticias │  │  Seleccionar Documentos              │  📤 Subir Archivo    │ │
│  📅Agenda   │  │                                      │  (Paso 3)            │ │
│  🔄Comparad→│  │  ORIGINAL             →   ENMIENDAS  │                      │ │
│             │  │  ┌─────────────┐         ┌──────────┐│  Soporta PDF/DOCX   │ │
│  🛡️Admin    │  │  │ Seleccionar │  →      │Seleccion ││                      │ │
│             │  │  │ 📅 01/01/26 │         │📅15/01/26││  [Nombre versión]   │ │
│  🚪Logout   │  │  │ Radicación  │         │Entirillad││  [Seleccionar PDF]  │ │
│             │  │  └─────────────┘         └──────────┘│  [+ Añadir Versión] │ │
└─────────────┤  │                                      │                      │ │
              │  │  [🔄 Ver Diferencias] [🤖 IA]       │                      │ │
              │  └──────────────────────────────────────┴──────────────────────┘ │
              │                                                                   │
              │  ┌─────────────────────────────────────────────────────────────┐ │
              │  │  🔀 Comparativa Textual          [❌ Eliminado] [✅ Añadido] │ │
              │  ├─────────────────────────────────────────────────────────────┤ │
              │  │  Nº │ ORIGINAL              │ Nº │ MODIFICADO             │ │
              │  │  1  │ Artículo 1.- Esta ley │ 1  │ Artículo 1.- Esta ley  │ │
              │  │  2  │ establecerá medidas   │ 2  │ establecerá medidas    │ │
              │  │  3  │ para proteger ████    │ 3  │ para proteger y        │ │ ← Verde
              │  │     │                       │    │     fortalecer ████    │ │
              │  │  4  │ ████████████████████  │    │                        │ │ ← Rojo tachado
              │  │  5  │ los derechos          │ 4  │ los derechos           │ │
              │  └─────────────────────────────────────────────────────────────┘ │
              │                                                                   │
              │  ┌─────────────────────────────────────────────────────────────┐ │
              │  │  🧠 Resumen Jurídico (IA)                                   │ │
              │  ├─────────────────────────────────────────────────────────────┤ │
              │  │                                                             │ │
              │  │  Análisis de cambios principales:                          │ │
              │  │                                                             │ │
              │  │  • Se añade énfasis en "fortalecer" además de proteger...  │ │
              │  │  • Se elimina referencia a medidas temporales...           │ │
              │  │  • El artículo 3 introduce nuevas sanciones...             │ │
              │  │                                                             │ │
              │  └─────────────────────────────────────────────────────────────┘ │
              │                                                                   │
              └───────────────────────────────────────────────────────────────────┘
```

---

## Componentes Visuales Detallados

### Dropdown de Versiones

```
┌────────────────────────────┐
│ -- Seleccionar --          │
├────────────────────────────┤
│ 📅 01/01/2026 - Radicación │
│ 📅 15/01/2026 - Entirillado│
│ 📅 30/01/2026 - Aprobado   │
│ 📅 05/02/2026 - Ley Final  │
└────────────────────────────┘
```

### Tabla Diff (Detalle)

```
┌────┬─────────────────────┬────┬─────────────────────┐
│ Nº │ ORIGINAL            │ Nº │ MODIFICADO          │
├────┼─────────────────────┼────┼─────────────────────┤
│ 10 │ regular text        │ 10 │ regular text        │ ← Texto normal
│ 11 │ deleted line ——————│    │                     │ ← Rojo tachado
│ 12 │ changed text old ▓▓│ 11 │ changed text new ▓▓ │ ← Amarillo resaltado
│    │                     │ 12 │ new added line ▓▓▓▓ │ ← Verde
│ 13 │ regular text        │ 13 │ regular text        │ ← Texto normal
└────┴─────────────────────┴────┴─────────────────────┘

Leyenda:
▓▓ = Fondo de color (verde/rojo/amarillo)
—— = Texto tachado (eliminado)
```

### Estados de Botones

**Estado Normal:**
```
┌───────────────────┐  ┌──────────────────────────┐
│ 🔄 Ver Diferencias│  │ 🤖 Explicar Cambios (IA) │
│   (Gris oscuro)   │  │      (Púrpura)           │
└───────────────────┘  └──────────────────────────┘
```

**Estado Hover:**
```
┌───────────────────┐  ┌──────────────────────────┐
│ 🔄 Ver Diferencias│  │ 🤖 Explicar Cambios (IA) │
│  (Gris más oscuro)│  │   (Púrpura más oscuro)   │
└───────────────────┘  └──────────────────────────┘
       ↑ cursor             ↑ cursor
```

---

## Flujo de Interacción

```
Usuario ingresa URL
        │
        ▼
    /comparador/
        │
        ├─────────────────────┐
        │                     │
        ▼                     ▼
   Sin proyectos        Lista proyectos
        │                     │
        ▼                     ▼
   Mensaje vacío        Click proyecto
        │                     │
        ▼                     ▼
   "No hay datos"    /comparador/<id>/
                            │
                            ├──────────────┬──────────────┐
                            ▼              ▼              ▼
                     Seleccionar V1  Seleccionar V2  Subir nuevo
                            │              │              │
                            └──────┬───────┘              │
                                   ▼                      ▼
                           Click "Ver Dif"         Formulario POST
                                   │                      │
                    ┌──────────────┼──────┐              │
                    ▼              ▼      ▼              ▼
               Sin IA         Con IA      │       Archivo guardado
                    │              │      │              │
                    ▼              ▼      │              │
             Solo Diff    Diff + IA       │              │
                    │              │      │              │
                    └──────┬───────┘      │              │
                           ▼              │              │
                    Resultados mostrados  │              │
                           │              │              │
                           └──────────────┴──────────────┘
                                          │
                                          ▼
                                  Página recargada
                                   con nueva versión
```

---

## Paleta de Colores Visual

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   SIDEBAR   │  │   TARJETAS  │  │   ORIGINAL  │  │  ENMIENDAS  │
│             │  │             │  │             │  │             │
│  #1e293b   │  │   #ffffff   │  │  #f9fafb    │  │  #dbeafe    │
│  Slate-900  │  │   White     │  │  Gray-50    │  │  Blue-50    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    DIFF+    │  │    DIFF-    │  │   DIFF CHG  │  │     IA      │
│             │  │             │  │             │  │             │
│  #dcfce7   │  │  #fee2e2    │  │  #fef9c3    │  │  #a855f7    │
│  Green-100  │  │  Red-100    │  │  Yellow-100 │  │  Purple-600 │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Responsividad

### Desktop (> 1024px)
```
┌───────┬─────────────────────────┐
│       │                         │
│ Side  │    Contenido (2/3)      │
│ bar   │    + Upload (1/3)       │
│       │                         │
└───────┴─────────────────────────┘
```

### Tablet (768px - 1024px)
```
┌───────┬─────────────────┐
│       │                 │
│ Side  │   Contenido     │
│ bar   │   Stack vertical│
│       │                 │
└───────┴─────────────────┘
```

### Mobile (< 768px)
```
┌─────────────────┐
│   Hamburger     │
├─────────────────┤
│                 │
│   Contenido     │
│   Full width    │
│   Stack         │
│                 │
└─────────────────┘
```

---

## Animaciones y Transiciones

### Efectos CSS aplicados:

1. **Hover en tarjetas**: `transition-colors` (suave cambio de color)
2. **Hover en botones**: `transition` (todas las propiedades)
3. **Resultados**: `animate-fade-in-up` (aparición animada)
4. **Sidebar activo**: Resaltado con `bg-blue-900`

### Tiempos de transición:
- Cambios de color: ~150ms
- Efectos de escala: ~200ms
- Aparición de contenido: ~300ms

---

## Iconografía (Font Awesome)

| Elemento | Icono | Código FA |
|----------|-------|-----------|
| Logo | ⚖️ | fa-balance-scale |
| Dashboard | 📊 | fa-chart-pie |
| Noticias | 📰 | fa-newspaper |
| Calendario | 📅 | fa-calendar-alt |
| Comparador | 🔄 | fa-exchange-alt |
| Admin | 🛡️ | fa-user-shield |
| Logout | 🚪 | fa-sign-out-alt |
| Diff textual | 🔀 | fa-code-branch |
| IA | 🤖 | fa-robot |
| Cerebro (IA) | 🧠 | fa-brain |
| Subir archivo | 📤 | fa-cloud-upload-alt |
| Añadir | ➕ | fa-plus |
| Volver | ⬅️ | fa-arrow-left |
| Siguiente | ➡️ | fa-arrow-right |

---

## Conclusión Visual

El diseño del comparador combina:
- ✅ Jerarquía visual clara (sidebar oscuro vs contenido claro)
- ✅ Código de colores intuitivo (verde = añadido, rojo = eliminado)
- ✅ Separación clara de funciones (Original vs Enmiendas)
- ✅ Feedback visual inmediato (hover states, transiciones)
- ✅ Diseño profesional y moderno (Tailwind CSS, tipografía Inter)

El resultado es una interfaz que facilita la tarea compleja de comparar documentos legales extensos de manera visual y comprensible.
