from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
from fmpy import simulate_fmu, read_model_description

# Ruta del archivo FMU exportado desde Modelica
FMU_PATH = r"pump_v3_basicCold_t.fmu"

# Parámetros que se intentarán modificar antes de correr la simulación
START_VALUES = {
    # Temperatura inicial del loop de agua [K]
    "T_init": 273.15 + 2.3,

    # Flujo másico nominal [kg/s]
    # Depende de la bomba, pérdidas de carga y longitud total del sistema
    "m_flow_nominal": 0.114,

    # Temperatura del ambiente frío en la zona cold [K]
    "Tcold": 273.15 - 18.0,

    # Temperatura del entorno de las tuberías supply y return [K]
    # En laboratorio puede representar aire (~21°C)
    # En instalación real puede representar suelo (~8°C)
    "T_amb": 273.15 + 21.0,

    # Temperatura inicial del agua del reservorio [K]
    "T_water": 273.15 + 7.4,

    # Temperatura externa asociada al entorno del reservorio [K]
    "T_ground": 273.15 + 8.0,

    # Material del tramo frío:
    # 1=Cobre, 2=PVC, 3=HDPE, 4=Valco
    "material_cold": 2,

    # Material del tramo dentro del reservorio:
    # 1=Cobre, 2=PVC, 3=HDPE, 4=Valco
    "material_heat": 1,

    # Largo del tramo de tubería expuesto al ambiente frío [m]
    "L_cold": 1.0,

    # Largo de tuberías supply y return [m]
    # Conceptualmente representan tuberías enterradas
    "L": 1.0,

    # Largo de tubería dentro del reservorio [m]
    "L_heat": 1.5,

    # Potencia térmica entregada por la bomba al fluido [W]
    "P_pumpHeat": 19.0,
}

# Tiempo total de simulación: 72 horas
STOP_TIME = 72 * 3600

# Paso de salida del FMU
# Se comprobó que 0.2 s funciona estable
OUTPUT_INTERVAL = 0.2

# Mostrar gráficos en pantalla
SHOW_PLOTS = True

# Variables que se intentan extraer del FMU
CANDIDATE_OUTPUTS = [
    # Temperatura entrada tramo frío
    "SenTempIn_cold.T",

    # Temperatura salida tramo frío
    "senTemOut_cold.T",

    # Temperatura entrada tramo heat
    "senTemIn_heat.T",

    # Temperatura salida tramo heat
    "senTemOut_heat.T",

    # Temperatura del reservorio
    "Water_Reserv.T",

    # Flujo másico
    "senMasFlo.m_flow",

    # Flujo térmico del tramo frío
    "Q_cold_W",

    # Flujo térmico del tramo heat solo por tubería/reservorio
    "Q_heat_pipe_W",

    # Aporte térmico de la bomba
    "Q_pump_W",

    # Potencia térmica total de la zona heat
    "Q_heat_total_W",
]

def parse_unsettable_from_exception(exc: Exception):
# no modificar
    text = str(exc)
    m = re.search(r"could not be set:\s*(.+)$", text)
    if not m:
        return []
    return [x.strip() for x in m.group(1).split(",") if x.strip()]

def simulate_with_retry(fmu_path: Path, start_values: dict, outputs: list):
#no modificar
    current_values = dict(start_values)

    while True:
        try:
            result = simulate_fmu(
                filename=str(fmu_path),
                start_time=0.0,
                stop_time=STOP_TIME,
                output_interval=OUTPUT_INTERVAL,
                start_values=current_values if current_values else None,
                output=outputs,
            )
            return result, current_values
        except Exception as exc:
            bad = parse_unsettable_from_exception(exc)
            if not bad:
                raise

            removed_any = False
            for name in bad:
                if name in current_values:
                    print(f"[AVISO] El FMU no permite ajustar '{name}'. Se elimina y se reintenta.")
                    current_values.pop(name, None)
                    removed_any = True

            if not removed_any:
                raise

def main():
    # Verificar que exista el FMU
    fmu_path = Path(FMU_PATH).resolve()
    if not fmu_path.exists():
        raise FileNotFoundError(f"No existe el FMU: {fmu_path}")

    print("========================================")
    print("SIMULACION FMU PARAMETRICO")
    print("========================================")
    print(f"FMU             : {fmu_path}")
    print(f"Stop time       : {STOP_TIME} s")
    print(f"Output interval : {OUTPUT_INTERVAL} s")
    print("========================================")

    # Leer descripción interna del FMU
    md = read_model_description(str(fmu_path))
    variable_names = [v.name for v in md.modelVariables]

    # Mostrar qué parámetros se quieren aplicar
    print("\n===== PARAMETROS SOLICITADOS =====")
    for k, v in START_VALUES.items():
        exists = "SI" if k in variable_names else "NO"
        print(f"{k:<18} = {str(v):<12} | existe en FMU: {exists}")

    # Solo pedir salidas que realmente existan en el FMU
    outputs = [name for name in CANDIDATE_OUTPUTS if name in variable_names]

    print("\n===== SALIDAS DISPONIBLES =====")
    for name in outputs:
        print(f"  - {name}")

    # Simulación con reintento
    result, applied_values = simulate_with_retry(
        fmu_path=fmu_path,
        start_values=START_VALUES,
        outputs=outputs,
    )

    print("\n===== PARAMETROS FINALMENTE APLICADOS =====")
    for k, v in applied_values.items():
        print(f"{k:<18} = {v}")

    # Convertir resultado a DataFrame
    df = pd.DataFrame({name: result[name] for name in result.dtype.names})
    df["time_h"] = df["time"] / 3600.0

    # Convertir temperaturas de K a °C
    temp_vars = [c for c in df.columns if c.endswith(".T")]
    for var in temp_vars:
        df[var.replace(".T", "_C")] = df[var] - 273.15

    # Guardar resultados completos
    out_csv = fmu_path.with_name("resultados_fmu_param.csv")
    df.to_csv(out_csv, index=False)

    print("\n===== TEMPERATURAS FINALES A 72 h =====")
    for col in df.columns:
        if col.endswith("_C"):
            print(f"{col:<22} = {df[col].iloc[-1]:10.3f} °C")

    print("\n===== Q FINALES A 72 h =====")
    for col in ["Q_cold_W", "Q_heat_pipe_W", "Q_pump_W", "Q_heat_total_W"]:
        if col in df.columns:
            print(f"{col:<22} = {df[col].iloc[-1]:10.3f} W")

    print(f"\nCSV guardado en: {out_csv}")

    # Gráfico de temperaturas
    plt.figure(figsize=(10, 6))
    for col in df.columns:
        if col.endswith("_C"):
            plt.plot(df["time_h"], df[col], label=col)
    plt.xlabel("Tiempo [h]")
    plt.ylabel("Temperatura [°C]")
    plt.title("Temperaturas de sensores")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fmu_path.with_name("temperaturas_fmu_param.png"), dpi=150)
    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close()

    # Gráfico de potencias térmicas
    q_cols = [c for c in ["Q_cold_W", "Q_heat_pipe_W", "Q_pump_W", "Q_heat_total_W"] if c in df.columns]
    if q_cols:
        plt.figure(figsize=(10, 6))
        for col in q_cols:
            plt.plot(df["time_h"], df[col], label=col)
        plt.xlabel("Tiempo [h]")
        plt.ylabel("Q [W]")
        plt.title("Potencias térmicas por tramo")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(fmu_path.with_name("Q_fmu_param.png"), dpi=150)
        if SHOW_PLOTS:
            plt.show()
        else:
            plt.close()

if __name__ == "__main__":
    main()