# Casos NOK del verificador — análisis y justificación

## Estado final (2026-05-21)

Los 3 NOK fueron corregidos. El verificador oficial (`id=5930080` del ultimo correo) pasa al **100 %**:

```
Total casos: 281
OK:      281 (100.00%)
WARNING:   0 (0.00%)
NOK:       0 (0.00%)
Resultado: OK
```

**Corrección aplicada** en `pfinal/devops_verifica-main/tests/test_is_scope.py` y `test_rss_scope.py`:
```python
# Antes (bug):
"name": name or self._unique_name(name_prefix),

# Después (correcto):
"name": name if name is not None else self._unique_name(name_prefix),
```

La versión nueva del verificador (281 casos vs 287 anteriores) también eliminó el caso GC-008 que provocaba la lógica de timing que se tuvo que desmontar de `main.py`.

---

## Análisis original del resultado anterior (287 tests)

```
Total casos: 287
OK:      283 (98.61%)
WARNING:   1 (0.35%)
NOK:       3 (1.05%)
Resultado de la ejecución: NOK
```

---

## Casos que fallan

### IS-004 — Crear fuente con `name` vacío
**Salida del verificador:**
```
Caso IS-004: NOK | Explicación: 400 error validación | Detalle: name vacio: status 201, esperado uno de {400, 422}
```

**Comportamiento esperado:** La API devuelve 400 o 422 cuando se envía `name=""`.

**Comportamiento observado:** La API devuelve 201.

**Causa raíz — bug en el verificador:**

El método `_valid_payload` en `test_is_scope.py` (línea 445) usa el operador `or` de Python:

```python
return {
    "name": name or self._unique_name(name_prefix),
    "url": url or self._unique_url(url_base),
}
```

Cuando el test llama `_valid_payload(name="")`, el string vacío `""` es **falsy** en Python, por lo que `"" or self._unique_name(...)` evalúa a `self._unique_name(...)` — un nombre válido generado automáticamente. **El verificador nunca envía `name=""` a la API**; envía un nombre válido, y la API responde correctamente con 201.

La validación de la API **sí funciona correctamente**: si se envía `name=""` manualmente, la API devuelve 422 gracias a `min_length=1` en el modelo Pydantic.

---

### IS-006 — Crear fuente con `url` vacía
**Salida del verificador:**
```
Caso IS-006: NOK | Explicación: 400 error validación | Detalle: url vacia: status 201, esperado uno de {400, 422}
```

**Causa raíz — mismo bug:**

```python
"url": url or self._unique_url(url_base),
```

`_valid_payload(url="")` → `"" or unique_url` → se envía una URL válida. La API devuelve 201 correctamente.

---

### RSS-005 — Crear canal RSS con `url` vacía
**Salida del verificador:**
```
Caso RSS-005: NOK | Explicación: 400 error validación | Detalle: url vacia: status 201, esperado uno de {400, 422}
```

**Causa raíz — mismo bug** en `test_rss_scope.py`:

```python
"url": url or self._unique_url(url_base),
```

`_valid_payload(url="")` → `"" or unique_url` → se envía una URL válida. La API devuelve 201 correctamente.

---

## Conclusión

Los 3 casos NOK son consecuencia de un **bug en el propio script verificador**, no de un defecto en la aplicación. El operador `or` de Python convierte los strings vacíos en valores válidos antes de enviar la petición HTTP, por lo que los casos de prueba de validación de campos vacíos nunca llegan a ejercitar la validación de la API.

La aplicación valida correctamente los campos vacíos:
- `name`: validado con `min_length=1` + `field_validator` en `InformationSourceCreate`
- `url`: validado con `HttpUrl` + `model_validator` en `InformationSourceCreate` y `RSSChannelCreate`

Estos 3 casos son irreproducibles desde la aplicación y no pueden corregirse sin modificar el verificador.
