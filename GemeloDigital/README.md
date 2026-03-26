# README --- Simulación FMU `pump_v3_basicCold_t`

Hola Javi,

Te dejo explicado todo de forma clara para que puedas correr el modelo,
modificarlo y también eventualmente integrarlo en un servicio si lo
necesitas.



------------------------------------------------------------------------

# 1. Qué representa el modelo

Este modelo simula un circuito cerrado de agua con transferencia de
calor.

El sistema tiene 4 zonas:

1.  **Cold**
    -   Tubería expuesta a un ambiente frío (ej: cámara a -18°C)
    -   Aquí el fluido pierde calor
2.  **Supply / Return**
    -   Tuberías que conectan el sistema
    -   En laboratorio están al aire
    -   En la vida real normalmente estarían enterradas
3.  **Heat (reservorio)**
    -   Tubería sumergida en agua
    -   Aquí el fluido gana calor
4.  **Bomba**
    -   Mueve el fluido
    -   Además introduce calor al sistema

------------------------------------------------------------------------

# 2. Instalación


Instalar librerías:

pip install fmpy pandas matplotlib

------------------------------------------------------------------------

# 3. Archivo necesario

Necesitas tener:

pump_v3_basicCold_t.fmu

------------------------------------------------------------------------

# 4. Parámetros del modelo (IMPORTANTE)

Todos estos parámetros están pensados para que los puedas modificar.

------------------------------------------------------------------------

## T_init

Temperatura inicial de TODO el circuito.

Unidad: Kelvin

Esto define desde dónde parte la simulación.

------------------------------------------------------------------------

## m_flow_nominal

Flujo másico del sistema (kg/s)

Esto depende directamente de: - la bomba - pérdidas de carga - longitud
del sistema

Este valor viene del experimento, pero en la realidad puede cambiar
bastante.

------------------------------------------------------------------------

## Tcold

Temperatura del ambiente frío.

Ejemplo: cámara a -18°C

Es lo que enfría el tramo cold.

------------------------------------------------------------------------

## T_amb

Temperatura de las tuberías supply y return.

Aquí hay algo importante:

En laboratorio: → estaban al aire → usar \~21°C

En sistema real: → estarían enterradas → usar \~8°C

O sea, este parámetro en realidad puede representar: - aire
(experimento) - suelo (instalación real)

------------------------------------------------------------------------

## T_water

Temperatura inicial del agua del reservorio.

Solo afecta condición inicial.

------------------------------------------------------------------------

## T_ground

Temperatura del entorno del reservorio.

Esto es el aire/suelo alrededor del tanque.

------------------------------------------------------------------------

## material_cold y material_heat

Material de las tuberías.

Valores:

1 → Cobre\
2 → PVC\
3 → HDPE\
4 → Valco

Esto cambia directamente la conductividad térmica.

------------------------------------------------------------------------

## L_cold

Longitud de tubería en zona fría.

Es la tubería expuesta al frío.

------------------------------------------------------------------------

## L

Longitud de supply y return.

Estas son las tuberías intermedias.


------------------------------------------------------------------------

## L_heat

Longitud de tubería dentro del reservorio.

Esto define cuánto intercambio hay con el agua.

------------------------------------------------------------------------

## P_pumpHeat

Potencia térmica de la bomba (W).

Esto es CLAVE:

La bomba no solo mueve agua, también calienta el fluido.

Este calor se suma en la zona caliente.

------------------------------------------------------------------------

# 5. Outputs (salidas del modelo)

Estas variables son las que deberías leer del FMU.

------------------------------------------------------------------------

## Temperaturas

-   SenTempIn_cold.T → entrada zona fría
-   senTemOut_cold.T → salida zona fría
-   senTemIn_heat.T → entrada zona caliente
-   senTemOut_heat.T → salida zona caliente
-   Water_Reserv.T → temperatura del reservorio

------------------------------------------------------------------------

## Flujo

-   senMasFlo.m_flow → flujo másico

------------------------------------------------------------------------

## Flujos de calor 

-   Q_cold_W → calor intercambiado en tramo frío
-   Q_heat_pipe_W → calor en tubería del reservorio
-   Q_pump_W → calor de la bomba
-   Q_heat_total_W → total en zona caliente

Esto permite hacer balance energético.

------------------------------------------------------------------------

# 6. Resultados

El script genera:

-   CSV con todas las variables
-   gráfico de temperaturas
-   gráfico de potencias térmicas

------------------------------------------------------------------------

# 7. Notas importantes

-   Usar output_interval = 0.2 (más grande puede fallar)
-   El script elimina automáticamente parámetros que el FMU no acepta
-   Todo está en unidades SI

------------------------------------------------------------------------

# 8. Cómo usar esto bien

Puedes usar este modelo para:

-   ajustar contra datos reales
-   probar distintos materiales
-   ver impacto del flujo
-   comparar laboratorio vs instalación real
-   integrarlo en backend/API

------------------------------------------------------------------------


