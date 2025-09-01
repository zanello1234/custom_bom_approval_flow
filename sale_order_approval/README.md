# Sale Order Approval Workflow

Este módulo agrega un estado "Aprobada" requerido antes de confirmar órdenes de venta.

## Características

### 🎯 Estado "Aprobada" Obligatorio
- Estado requerido entre cotización y confirmación
- Botón "Aprobar" para transición a estado aprobado
- Botón "Confirmar" solo disponible después de aprobación

### 📋 Flujo de Trabajo
1. **Borrador/Enviada** → *Aprobar* → **Aprobada**
2. **Aprobada** → *Confirmar* → **Orden de Venta** (crea entregas/OM)

### 🔧 Funcionalidades
- Control obligatorio de aprobación antes de confirmación
- Mensajes claros en el chatter para seguimiento
- Vista dedicada para órdenes aprobadas
- Indicadores visuales para el estado aprobado

## Instalación

1. Instala el módulo desde Aplicaciones
2. El flujo de aprobación se aplicará automáticamente

## Uso

1. **Crear Cotización**: Como siempre
2. **Aprobar**: Usa "Aprobar" cuando la cotización esté lista
3. **Confirmar**: Usa "Confirmar" solo en órdenes aprobadas

## Beneficios

- **Control de Calidad**: Aprobación obligatoria antes de producción
- **Compliance**: Mejor seguimiento de autorizaciones
- **Reducción de Errores**: Menos órdenes incorrectas en producción
