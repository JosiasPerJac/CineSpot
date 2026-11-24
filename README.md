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



## Simulación de reservas concurrentes

Desde la raíz del proyecto, ejecuta estos comandos con Python 3 (en Windows puedes usar `py`). La simulación usa solo la biblioteca estándar.

```text
python reservas_concurrentes.py
python -m unittest -v
```

### Datos de entrada

La función, sus asientos y las solicitudes se leen de `funcion.json`. Puedes editar ese archivo (agregar clientes, asientos o cambiar qué asiento pide cada uno) o pasar otro archivo como argumento: `python reservas_concurrentes.py otra_funcion.json`. Cada solicitud se atiende en su propio hilo y todos arrancan a la vez, como si los clientes pulsaran "reservar" al mismo tiempo. Entre validar el asiento y registrarlo, cada hilo espera un tiempo aleatorio que representa el cobro.

### Caso de error y caso de éxito

1. **Primera ejecución (error).** Con `USAR_LOCK = False` (valor inicial, al inicio de `reservas_concurrentes.py`), los hilos leen el mismo estado antes de que alguno escriba. La auditoría final detecta la sobreventa, imprime `FALLO` y el programa termina con código de salida 1.
2. **Corrección.** Cambia la línea a `USAR_LOCK = True`.
3. **Segunda ejecución (éxito).** El `threading.Lock` convierte la lectura, la validación y la escritura en una sola sección crítica. Los demás hilos leen el estado ya actualizado y son rechazados. La auditoría imprime `ÉXITO` y el programa termina con código 0.

Nada del resultado está escrito de antemano. Cada línea del registro se imprime cuando el hilo la produce, con el tiempo transcurrido y el nombre del hilo. La auditoría compara las confirmaciones con el estado que quedó realmente en memoria. Por eso el orden de los hilos y el titular final cambian entre ejecuciones.

### Sección crítica y exclusión mutua

La sección crítica empieza al consultar el recurso, incluye la validación de disponibilidad y termina al actualizar el contador o registrar al titular. `Cupos` almacena la disponibilidad en un entero; `Asientos` usa un diccionario con el asiento como clave y el titular como valor (`None` = libre). Sin exclusión mutua, con el entero varios hilos calculan el mismo saldo y las escrituras se pierden; con el diccionario, varios clientes reciben confirmación del mismo asiento y la última escritura sobrescribe a las anteriores.

### Ejemplo de ejecución

Salida de una ejecución real (Python 3, macOS). Los tiempos y el orden varían en cada corrida.

Sin `Lock`:

```text
=== Diccionario (Asientos) ===
  [    0.4 ms] hilo-Pedro     Pedro lee A2 -> libre
  [    0.5 ms] hilo-Ana       Ana lee A1 -> libre
  [    0.5 ms] hilo-Luis      Luis lee A1 -> libre
  [    0.5 ms] hilo-Marta     Marta lee A1 -> libre
  [   67.3 ms] hilo-Luis      Luis escribe A1 = Luis -> CONFIRMADO
  [  107.7 ms] hilo-Marta     Marta escribe A1 = Marta -> CONFIRMADO
  [  136.4 ms] hilo-Ana       Ana escribe A1 = Ana -> CONFIRMADO
  [  136.6 ms] hilo-Pedro     Pedro escribe A2 = Pedro -> CONFIRMADO
  Confirmadas: Ana, Luis, Marta, Pedro
  Estado final: {'A1': 'Ana', 'A2': 'Pedro'}
  ERROR: A1 se confirmó a 3 clientes (Ana, Luis, Marta); solo quedó registrado Ana. Luis y Marta pagaron sin asiento

Resultado: FALLO - hubo reservas duplicadas. Cambia USAR_LOCK = True y vuelve a ejecutar.
```

Con `Lock`:

```text
=== Diccionario (Asientos) ===
  [    0.6 ms] hilo-Pedro     Pedro lee A2 -> libre
  [   82.8 ms] hilo-Pedro     Pedro escribe A2 = Pedro -> CONFIRMADO
  [   83.0 ms] hilo-Ana       Ana lee A1 -> libre
  [  193.7 ms] hilo-Ana       Ana escribe A1 = Ana -> CONFIRMADO
  [  193.9 ms] hilo-Luis      Luis lee A1 -> Ana
  [  193.9 ms] hilo-Luis      Luis RECHAZADO: A1 ya es de Ana
  [  194.0 ms] hilo-Marta     Marta lee A1 -> Ana
  [  194.1 ms] hilo-Marta     Marta RECHAZADO: A1 ya es de Ana
  Confirmadas: Ana, Pedro
  Estado final: {'A1': 'Ana', 'A2': 'Pedro'}
  OK: cada cupo/asiento se confirmó a un solo cliente

Resultado: ÉXITO - no hubo reservas duplicadas.
```

Las seis pruebas automatizadas comprueban que la auditoría detecta los duplicados sin `Lock`, que no los hay con `Lock`, que un asiento inexistente se rechaza y que la ejecución completa falla sin `Lock` y pasa con él.
