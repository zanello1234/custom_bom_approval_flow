# Delivery Merge Components

## 🎯 Objetivo
Módulo específico para fusionar componentes duplicados en órdenes de delivery (transferencias de stock).

## ✨ Características
- **Botón de Fusión**: Botón intuitivo en la sección de operaciones de delivery orders
- **Agrupación Inteligente**: Agrupa productos idénticos por producto, ubicación, UOM y línea de venta
- **Consolidación de Cantidades**: Suma automáticamente las cantidades de elementos duplicados
- **Manejo de Reservas**: Gestiona correctamente las reservas de stock durante la fusión
- **Interfaz Limpia**: Botón bien ubicado y visible en la vista de operaciones

## 🔄 Cómo Funciona
1. **Identifica Duplicados**: Encuentra productos con mismo producto, ubicación, UOM y línea de venta
2. **Consolida**: Fusiona líneas duplicadas en una sola línea con cantidad total
3. **Limpia**: Elimina automáticamente las líneas duplicadas vacías
4. **Preserva Datos**: Mantiene toda la información importante (ubicaciones, reservas, etc.)

## 📋 Uso
1. Ve a una delivery order (Inventario > Operaciones > Transferencias)
2. En la pestaña "Operaciones", encontrarás el botón "🔄 Fusionar Componentes Duplicados"
3. Haz clic en el botón para consolidar automáticamente los componentes duplicados
4. Recibirás una notificación con el resultado de la operación

## 🛠️ Instalación
1. Copia el módulo a tu directorio de addons de Odoo
2. Actualiza la lista de módulos en Odoo
3. Instala el módulo "Delivery Merge Components"

## 📦 Dependencias
- `stock`: Módulo de inventario de Odoo

## 🔧 Compatibilidad
- Odoo 18.0
- Compatible con workflows estándar de inventario de Odoo
