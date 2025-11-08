# Frontend Best Practices - Lecciones Aprendidas

Este documento contiene las mejores prácticas y errores comunes a evitar basados en la experiencia del desarrollo del frontend admin.

## 🔴 Errores Críticos a Evitar

### 1. Servicios API (axios)

**✅ SIEMPRE hacer:**
```typescript
// Configurar baseURL
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

// Agregar interceptor de autenticación
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Manejar errores 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**❌ NUNCA hacer:**
- Olvidar configurar baseURL
- No agregar interceptores de autenticación
- No manejar errores 401

---

### 2. Formato de Fechas

**✅ SIEMPRE usar ISO 8601:**
```typescript
// Para enviar al backend
const isoDate = date.toISOString(); // "2024-01-15T10:30:00.000Z"

// Helper function
const toISOString = (date: Date | string): string => {
  return date instanceof Date ? date.toISOString() : new Date(date).toISOString();
};
```

**❌ NUNCA usar:**
```typescript
// ❌ Formato YYYY-MM-DD (causa errores 422)
const badDate = "2024-01-15";
```

---

### 3. Componentes Select (Radix UI)

**✅ SIEMPRE usar valores válidos:**
```typescript
<SelectItem value="all">Todos</SelectItem>
<SelectItem value="ACTIVO">Activo</SelectItem>

// En el estado
const [filter, setFilter] = useState<string>("all");

// Al filtrar
if (filter !== "all") {
  // aplicar filtro
}
```

**❌ NUNCA usar:**
```typescript
// ❌ Valores vacíos causan errores de validación
<SelectItem value="">Todos</SelectItem>
```

---

### 4. Hooks useEffect - Dependencias

**✅ SIEMPRE revisar dependencias:**
```typescript
// ✅ Solo incluir dependencias necesarias
useEffect(() => {
  loadData();
}, []); // Se ejecuta solo una vez

// ✅ Si necesitas una función, usa useCallback
const loadData = useCallback(() => {
  // lógica
}, [dependency1, dependency2]);

useEffect(() => {
  loadData();
}, [loadData]);
```

**❌ NUNCA hacer:**
```typescript
// ❌ Incluir funciones que cambian en cada render (loop infinito)
useEffect(() => {
  onFiltersChange(filters);
}, [filters, onFiltersChange]); // ❌ onFiltersChange causa loop
```

---

### 5. Backend - Tortoise ORM

**✅ SIEMPRE ejecutar queries:**
```typescript
// ✅ Usar .all() para obtener resultados
const items = await Model.filter(condition).all();

// ✅ Iterar sobre resultados
for (const item in items) {
  // procesar
}
```

**❌ NUNCA olvidar .all():**
```typescript
// ❌ Esto NO ejecuta la query
const items = await Model.filter(condition);
// items es un QuerySet, no una lista
```

---

### 6. Backend - Tortoise ORM Aggregations

**✅ SIEMPRE calcular manualmente:**
```python
# ✅ Obtener datos y calcular en Python
items = await Model.filter(condition).all()
average = sum(item.value for item in items) / len(items) if items else 0

# ✅ Contar manualmente
distribution = {}
for item in items:
    key = item.category
    distribution[key] = distribution.get(key, 0) + 1
```

**❌ NUNCA usar aggregate() o group_by():**
```python
# ❌ Tortoise ORM no soporta esto como Django
result = await Model.filter().aggregate(avg=Avg('field'))  # ❌ Error
grouped = await Model.all().group_by('field')  # ❌ Error
```

---

### 7. Backend - Serialización de Datos

**✅ SIEMPRE usar tipos correctos en Pydantic:**
```python
class MySchema(BaseModel):
    # ✅ Usar float para números decimales
    amount: float
    percentage: float
    
    # ✅ Convertir Decimal a float
    return MySchema(
        amount=float(decimal_value),
        percentage=float(percentage_value)
    )
```

**❌ NUNCA usar Decimal en schemas:**
```python
class MySchema(BaseModel):
    # ❌ Decimal se serializa como string en JSON
    amount: Decimal  # Resultado: "10.50" en lugar de 10.50
```

---

### 8. Backend - Rutas Dinámicas

**✅ SIEMPRE definir rutas específicas primero:**
```python
# ✅ Orden correcto
@router.get("/kpis")
async def get_kpis(): ...

@router.get("/ciudades")
async def get_ciudades(): ...

@router.get("/{id}")  # ✅ Al final
async def get_by_id(id: str): ...
```

**❌ NUNCA poner rutas dinámicas primero:**
```python
# ❌ Orden incorrecto
@router.get("/{id}")  # ❌ Captura todo, incluso "/kpis"
async def get_by_id(id: str): ...

@router.get("/kpis")  # ❌ Nunca se alcanza
async def get_kpis(): ...
```

---

### 9. Backend - Relaciones en Modelos

**✅ SIEMPRE usar rutas completas:**
```python
# ✅ Acceder a campos anidados correctamente
telefono = cliente.usuario.telefono  # ✅ Correcto

# ✅ Usar select_related para cargar relaciones
query = Model.all().select_related('relation')
```

**❌ NUNCA asumir campos directos:**
```python
# ❌ Si telefono está en usuario, no en cliente
telefono = cliente.telefono  # ❌ AttributeError
```

---

### 10. Backend - Conversión de UUIDs

**✅ SIEMPRE convertir UUID a string:**
```python
# ✅ Convertir UUID a string para JSON
return {
    "user_id": str(user.id),  # ✅ Correcto
    "data": {
        "id": str(item.id)  # ✅ Correcto
    }
}
```

**❌ NUNCA devolver UUID directamente:**
```python
# ❌ UUID no es serializable a JSON directamente
return {
    "user_id": user.id  # ❌ Puede causar errores
}
```

---

### 11. Backend - Campos Calculados

**✅ SIEMPRE incluir campos que el frontend espera:**
```python
# ✅ Si el frontend espera nombre_completo
return {
    "nombre": user.nombre,
    "apellido": user.apellido,
    "nombre_completo": f"{user.nombre} {user.apellido}"  # ✅ Agregar
}
```

**❌ NUNCA asumir que el frontend calculará:**
```python
# ❌ Frontend espera nombre_completo pero solo enviamos nombre y apellido
return {
    "nombre": user.nombre,
    "apellido": user.apellido
    # ❌ Falta nombre_completo
}
```

---

## 📋 Checklist para Nuevos Servicios

### Frontend Service
- [ ] Configurar baseURL con variable de entorno
- [ ] Agregar interceptor de autenticación
- [ ] Agregar interceptor de manejo de errores 401
- [ ] Usar ISO 8601 para fechas
- [ ] Validar tipos de respuesta

### Frontend Components
- [ ] Usar valores válidos en SelectItem (no strings vacíos)
- [ ] Revisar dependencias de useEffect
- [ ] Evitar loops infinitos
- [ ] Manejar estados de loading y error
- [ ] Validar que los campos existen antes de usar .toLowerCase() u otros métodos

### Backend Endpoints
- [ ] Rutas específicas antes de rutas dinámicas
- [ ] Convertir UUID a string
- [ ] Convertir Decimal a float
- [ ] Usar .all() en queries de Tortoise ORM
- [ ] Calcular aggregations manualmente
- [ ] Incluir campos calculados que el frontend espera
- [ ] Usar select_related para relaciones
- [ ] Validar rutas de campos anidados

---

## 🎯 Resumen de Errores Resueltos

1. ✅ PQR Service - baseURL y autenticación
2. ✅ Analytics Service - Formato de fechas ISO
3. ✅ SelectItem - Valores vacíos a "all"
4. ✅ Auth Endpoints - UUID a string
5. ✅ Asesores Endpoints - Queries ORM simplificadas
6. ✅ AsesoresFilters - Loop infinito
7. ✅ PQR Service - Campo telefono (relaciones)
8. ✅ Asesores KPIs - Missing .all()
9. ✅ Asesores Router - Route conflict
10. ✅ PQR Metrics - Tortoise ORM aggregate()
11. ✅ PQR Metrics - Decimal serialization
12. ✅ Admin Endpoints - User/Role Management APIs
13. ✅ GestionUsuarios - nombre_completo field

---

**Última actualización:** Sesión de corrección de errores frontend/backend
**Aplicar en:** Frontend Asesor y futuros desarrollos
