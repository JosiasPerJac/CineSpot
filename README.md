# CineSpot

## Integrantes

- Josias Perez
- Jorge Colamarco

## Descripción

CineSpot es un proyecto académico que se desarrollará en Python para simular una plataforma de reserva de asientos en una sala de cine. Permitirá consultar la disponibilidad de los asientos y solicitar la reserva de uno libre para una función determinada. Antes de confirmar cada solicitud, el sistema deberá validar el asiento y actualizar su estado.

El problema que se analiza es cómo mantener una disponibilidad confiable cuando varias solicitudes coinciden, de modo que un asiento no pueda asignarse más de una vez para la misma función.

## Análisis

Para analizar la coordinación, se considera que distintas solicitudes pueden atenderse al mismo tiempo. Cada solicitud debe comprobar el estado del asiento elegido y, si sigue disponible, reservarlo. Si dos solicitudes coinciden sobre el mismo asiento, ambas podrían leerlo como libre antes de que alguna registre el cambio. Por eso, la comprobación y la actualización deben coordinarse como una sola operación.

### Unidades de ejecución y recurso compartido

Cada unidad de ejecución representa un trabajador que procesa la solicitud de un usuario. El recurso compartido es el mapa de asientos de una función: registra cada asiento y su estado, disponible o reservado. El identificador de la función forma parte del registro, porque un mismo asiento puede estar disponible en una función y reservado en otra. Los trabajadores deben cooperar para consultar y cambiar ese estado sin duplicar asignaciones.

### Comparación de modelos

En memoria compartida, varios hilos acceden a datos comunes y los accesos concurrentes que pueden entrar en conflicto requieren sincronización (OpenMP Architecture Review Board, 2021). En el paso de mensajes, los procesos intercambian solicitudes y respuestas de forma explícita (Message Passing Interface Forum, 2023).

| Modelo | Aplicación en CineSpot | Ventajas y límites |
|---|---|---|
| Memoria compartida | Varios hilos atienden solicitudes y consultan el mismo mapa de asientos. Un `threading.Lock` protege la sección que verifica que el asiento esté disponible y lo cambia a reservado; Python documenta este bloqueo para sincronizar hilos (Python Software Foundation, s. f.-b). | Es directo para una simulación en un solo proceso y evita intercambiar mensajes por cada solicitud. Sin el bloqueo alrededor de la comprobación y el cambio, dos hilos podrían reservar el mismo asiento. |
| Paso de mensajes | Cada proceso trabajador envía la función, el asiento y el usuario por una `multiprocessing.Queue` a un coordinador. El coordinador es dueño del mapa, procesa una solicitud, valida el estado, lo actualiza si corresponde y devuelve una respuesta. Python ofrece colas para intercambiar datos entre procesos (Python Software Foundation, s. f.-a). | El mapa tiene un único responsable y los trabajadores no escriben directamente en él. A cambio, hay que gestionar mensajes y respuestas; el coordinador también puede convertirse en un punto de espera. |

### Conclusión del análisis

Para el alcance académico actual, se recomienda memoria compartida con hilos. La simulación mantiene el inventario de una función en una estructura común dentro de la aplicación; un bloqueo breve alrededor de la comprobación y la reserva permite proteger la operación que evita duplicados. Este diseño es directo y requiere menos coordinación adicional que una cola y un proceso administrador.

El paso de mensajes sería conveniente si CineSpot separara sus trabajadores en procesos o servicios independientes, pues un coordinador podría conservar la autoridad sobre el mapa de asientos. Para esta simulación, esa separación agregaría manejo de mensajes y respuestas que no resulta necesario. La recomendación se basa en el alcance descrito; no se afirma una ventaja de rendimiento medida.

## Bibliografía

- Message Passing Interface Forum. (2023). *MPI: A message-passing interface standard version 4.1*. https://www.mpi-forum.org/docs/mpi-4.1/mpi41-report/mpi41-report.htm
- OpenMP Architecture Review Board. (2021). *OpenMP application programming interface specification version 5.2*. https://www.openmp.org/spec-html/5.2/openmp.html
- Python Software Foundation. (s. f.-a). *multiprocessing - Process-based parallelism* (Python 3.14 documentation). Recuperado el 13 de octubre de 2026 de https://docs.python.org/3.14/library/multiprocessing.html
- Python Software Foundation. (s. f.-b). *threading - Thread-based parallelism* (Python 3.14 documentation). Recuperado el 13 de octubre de 2026 de https://docs.python.org/3.14/library/threading.html



## Interfaz por consola (Sprint 2)

La interfaz permite configurar, ejecutar y comparar las cuatro versiones de la solución concurrente. Solo usa la biblioteca estándar de Python 3.

```text
python interfaz_consola.py
python -m unittest -v
```

En Windows puedes usar `py` en lugar de `python`.

### Archivos

| Archivo | Contenido |
|---|---|
| `salas.py` | `SalaCineBasica` y `SalaCine`: estado de los asientos y reservas con o sin `Lock`. |
| `trabajador.py` | `TrabajadorReserva`: solicitud que ejecuta cada hilo y registro de su resultado. |
| `simulador.py` | `SimuladorCineSpot`: creación de la sala, ejecución de los hilos y detección de reservas duplicadas. |
| `interfaz_consola.py` | Menú interactivo, configuración y visualización de los hilos. |
| `test_reservas_concurrentes.py` | Pruebas automatizadas de las cuatro versiones. |

La interfaz llama al simulador, el simulador crea los trabajadores y cada
trabajador solicita una reserva a la sala. Las clases de sala se encargan
de consultar y actualizar el recurso compartido.

### Las cuatro versiones

| Opción | Recurso compartido | Sincronización |
|---|---|---|
| 1 | Básico: un entero (`0` disponible, `1` reservado) para un solo asiento | Sin `Lock` |
| 2 | Básico: un entero | Con `threading.Lock` |
| 3 | Complejo: diccionario `{asiento: {"estado", "usuario"}}` por función | Sin `Lock` |
| 4 | Complejo: diccionario | Con `threading.Lock` |

### Menú principal

```text
========== CineSpot · Reservas concurrentes ==========
Configuración: 3 hilos | Asientos: A1, A2, A3 | Asiento pedido: A1 | Demora: 100 ms
  1. Tipo básico (entero)        SIN Lock
  2. Tipo básico (entero)        CON Lock
  3. Tipo complejo (diccionario) SIN Lock
  4. Tipo complejo (diccionario) CON Lock
  5. Ejecutar y comparar las 4 versiones
  6. Cambiar configuración
  0. Salir
```

- **Opciones 1 a 4:** ejecutan una versión y muestran la tabla de hilos.
- **Opción 5:** ejecuta las cuatro versiones con la misma lista inicial de solicitudes y muestra una tabla comparativa. El tipo básico concentra todas las solicitudes en su único asiento, `A1`.
- **Opción 6:** cambia los parámetros. Al presionar Enter se conserva el valor actual.

| Parámetro | Descripción | Valor inicial |
|---|---|---|
| Número de hilos | Cada hilo atiende la solicitud de un usuario (`U01`, `U02`, ...). De 1 a 50. | `3` |
| Asientos de la sala | Lista separada por comas. Solo la usa el tipo complejo; el básico tiene un único asiento. | `A1,A2,A3` |
| Asiento pedido | En el tipo complejo, asiento que solicitan todos los hilos, o `aleatorio` para elegir uno de la sala por hilo. Un asiento inexistente produce `solicitud_invalida`. El tipo básico siempre utiliza `A1`. | `A1` |
| Demora (ms) | Tiempo simulado entre validar el asiento y registrarlo. Con `0` la carrera puede no aparecer. | `100` |

### Visualización de la ejecución de los hilos

Cada fila se imprime en el momento en que el hilo termina su operación, por eso el orden de las filas cambia entre ejecuciones.

| Columna | Significado |
|---|---|
| Hilo | Nombre del hilo (`Hilo-1`, `Hilo-2`, ...). |
| ID | Identificador del hilo en el sistema operativo (`threading.get_native_id()`). |
| Operación | Usuario y asiento que solicita, por ejemplo `U01 reserva A1`. |
| Estado antes | Estado del recurso que leyó el hilo antes de operar. |
| Resultado | `reserva_confirmada`, `asiento_ocupado` o `solicitud_invalida`. |
| Estado después | Estado del recurso después de la operación del hilo. |

Al final se muestran el **estado final del recurso compartido**, las reservas confirmadas y rechazadas, y si hubo una **condición de carrera** (un asiento confirmado a más de un usuario).

### Ejemplo: tipo complejo sin `Lock` (opción 3)

```text
--- Complejo (diccionario) SIN Lock | Función F01 ---
Estado inicial: A1=libre, A2=libre, A3=libre

Hilo     ID       Operación        Estado antes                 Resultado            Estado después
----------------------------------------------------------------------------------------------------------
Hilo-1   7123324  U01 reserva A1   A1=libre, A2=libre, A3=libre reserva_confirmada   A1=U01, A2=libre, A3=libre
Hilo-2   7123325  U02 reserva A1   A1=libre, A2=libre, A3=libre reserva_confirmada   A1=U02, A2=libre, A3=libre
Hilo-3   7123326  U03 reserva A1   A1=libre, A2=libre, A3=libre reserva_confirmada   A1=U03, A2=libre, A3=libre

Estado final del recurso: A1=U03, A2=libre, A3=libre
Confirmadas: 3 (U01, U02, U03) | Rechazadas: 0
CONDICIÓN DE CARRERA: A1 se confirmó a 3 usuarios (U01, U02, U03).
```

Los tres hilos leyeron `A1=libre` antes de que alguno escribiera, así que los tres recibieron confirmación y cada escritura sobrescribió a la anterior: en el estado final solo queda el último que escribió.

### Ejemplo: tipo complejo con `Lock` (opción 4)

```text
--- Complejo (diccionario) CON Lock | Función F01 ---
Estado inicial: A1=libre, A2=libre, A3=libre

Hilo     ID       Operación        Estado antes                 Resultado            Estado después
----------------------------------------------------------------------------------------------------------
Hilo-1   7123327  U01 reserva A1   A1=libre, A2=libre, A3=libre reserva_confirmada   A1=U01, A2=libre, A3=libre
Hilo-2   7123328  U02 reserva A1   A1=U01, A2=libre, A3=libre   asiento_ocupado      A1=U01, A2=libre, A3=libre
Hilo-3   7123329  U03 reserva A1   A1=U01, A2=libre, A3=libre   asiento_ocupado      A1=U01, A2=libre, A3=libre

Estado final del recurso: A1=U01, A2=libre, A3=libre
Confirmadas: 1 (U01) | Rechazadas: 2
Sin condición de carrera: cada asiento se confirmó a un solo usuario.
```

El `Lock` hace que la lectura, la validación y la escritura ocurran como una sola sección crítica: cada hilo ve el estado que dejó el anterior.

### Ejemplo: comparación de las cuatro versiones (opción 5)

```text
================ Comparación de las 4 versiones ================
Versión                          Confirmadas  ¿Carrera?  Estado final
Básico (entero) SIN Lock         3            Sí         1 (reservado)
Básico (entero) CON Lock         1            No         1 (reservado)
Complejo (diccionario) SIN Lock  3            Sí         A1=U01, A2=libre, A3=libre
Complejo (diccionario) CON Lock  1            No         A1=U01, A2=libre, A3=libre
```

### Evaluación del mecanismo de sincronización

- **Sin `Lock`**, las dos representaciones confirman el mismo asiento a varios usuarios. En el tipo básico el error ni siquiera queda registrado en el estado (solo guarda `1`); en el complejo, el último hilo en escribir sobrescribe a los demás.
- **Con `Lock`**, en ambas representaciones solo un hilo confirma cada asiento y el resto recibe `asiento_ocupado`.
- El tipo complejo conserva el usuario de cada asiento, por eso permite ver quién quedó registrado y detectar exactamente qué reservas se perdieron.
