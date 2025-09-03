# Test Script para Delivery Recreation

## Problema Reportado
El usuario reporta: "está cancelando el delivery pero no está recreando el delivery nuevo con la nueva bom"

## Solución Implementada

### Mejoras en _handle_delivery_update():

1. **Verificación Crítica**: 
   - Verifica que la línea de venta tenga flexible_bom_id asignado
   - Si no lo tiene, busca la BOM flexible más reciente y la asigna

2. **Método 1 - Stock Rule con Contexto**:
   - Usa `_action_launch_stock_rule()` con contexto de BOM flexible
   - Añade contexto: `force_flexible_bom=True`, `flexible_bom_id=X`
   - Commits cambios y verifica nuevas entregas

3. **Método 2 - Creación Manual**:
   - Si Método 1 falla, crea manualmente la entrega
   - Obtiene componentes directamente de la BOM flexible
   - Crea picking y moves para cada componente
   - Confirma la entrega

### Flujo de Prueba Recomendado:

1. **Crear Pedido**:
   ```
   - Producto: KIT con BOM base (ej: 3 componentes)
   - Cantidad: 1
   - Confirmar pedido → Se crea delivery #1 con BOM base
   ```

2. **Customizar BOM**:
   ```
   - Ir a "BOM Customization"
   - Modificar componentes (agregar/quitar/cambiar cantidades)
   - Habilitar "Cancel existing deliveries"
   - Crear BOM flexible
   ```

3. **Verificar Resultado**:
   ```
   - Delivery #1 debe estar cancelado
   - Delivery #2 debe crearse con componentes de BOM flexible
   - Componentes deben coincidir con la customización
   ```

### Logging para Debug:

Los logs mostrarán:
- `❌ CRITICAL: Sale order line does not have flexible_bom_id set!` (si hay problema)
- `✅ Sale line linked to flexible BOM: {id}` (si está bien)
- `🔄 Method 1: Using _action_launch_stock_rule()` (primer intento)
- `✅ Method 1 SUCCESS: Created deliveries: {names}` (si funciona)
- `🔄 Method 2: Manual delivery creation` (si método 1 falla)
- `✅ Method 2 SUCCESS: Created picking {name}` (creación manual exitosa)

### Puntos Clave:

1. **Asignación de BOM**: La BOM flexible DEBE estar asignada a sale_order_line_id.flexible_bom_id
2. **Contexto**: Se pasa el contexto de BOM flexible a todos los métodos
3. **Verificación**: Se verifica la creación exitosa antes de continuar
4. **Fallback**: Si el primer método falla, se usa creación manual garantizada
5. **Componentes**: Los moves creados reflejan exactamente los componentes de la BOM flexible

### Resultado Esperado:
- ✅ Entrega original cancelada
- ✅ Nueva entrega creada con BOM flexible
- ✅ Componentes correctos en la nueva entrega
- ✅ Usuario informado del resultado

Si el problema persiste, revisar los logs para identificar en qué método falla.
