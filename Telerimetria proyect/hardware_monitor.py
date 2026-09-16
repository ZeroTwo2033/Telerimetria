"""
hardware_monitor.py
--------------------
Módulo encargado de recolectar la información de rendimiento del sistema:
RAM, disco duro, procesador (uso + temperatura) y tarjeta gráfica (uso + temperatura).

Requiere:
    - psutil        (RAM, disco, CPU, temperaturas en Linux/Mac)
    - GPUtil         (uso de GPU NVIDIA, opcional)
    - wmi (solo Windows, opcional) para leer temperatura de CPU vía OpenHardwareMonitor

Si alguna fuente de datos no está disponible en el sistema operativo actual,
la función correspondiente devuelve None en ese campo en vez de fallar,
para que la interfaz gráfica pueda mostrar "No disponible".
"""

import platform
import shutil
import psutil

# --------------------------------------------------------------------------
# Umbrales de alerta (porcentaje). Se pueden ajustar a gusto.
# --------------------------------------------------------------------------
THRESHOLDS = {
    "ram": 85,
    "disk": 90,
    "cpu": 85,
    "gpu": 85,
}


# --------------------------------------------------------------------------
# RAM
# --------------------------------------------------------------------------
def get_ram_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "percent": mem.percent,
    }


# --------------------------------------------------------------------------
# DISCO
# --------------------------------------------------------------------------
def get_disk_info(path=None):
    if path is None:
        path = "C:\\" if platform.system() == "Windows" else "/"
    usage = shutil.disk_usage(path)
    percent = round(usage.used / usage.total * 100, 1)
    return {
        "path": path,
        "total_gb": round(usage.total / (1024 ** 3), 2),
        "used_gb": round(usage.used / (1024 ** 3), 2),
        "free_gb": round(usage.free / (1024 ** 3), 2),
        "percent": percent,
    }


# --------------------------------------------------------------------------
# CPU
# --------------------------------------------------------------------------
def _get_cpu_temp():
    """Intenta obtener la temperatura del CPU en distintas plataformas."""
    # Linux / algunos Mac vía psutil
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for key in ("coretemp", "k10temp", "cpu-thermal", "cpu_thermal", "zenpower"):
                if key in temps and temps[key]:
                    return round(temps[key][0].current, 1)
            # si no encontramos una clave conocida, usamos la primera disponible
            for entries in temps.values():
                if entries:
                    return round(entries[0].current, 1)
    except AttributeError:
        pass  # sensors_temperatures no existe en Windows/Mac
    except Exception:
        pass

    # Windows vía OpenHardwareMonitor + WMI (si el usuario lo tiene instalado y corriendo)
    if platform.system() == "Windows":
        try:
            import wmi  # requiere pywin32 + wmi instalados
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            for sensor in w.Sensor():
                if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                    return round(float(sensor.Value), 1)
        except Exception:
            pass

    return None  # no se pudo determinar


def get_cpu_info():
    percent = psutil.cpu_percent(interval=0.3)
    per_core = psutil.cpu_percent(interval=0.0, percpu=True)
    freq = psutil.cpu_freq()
    return {
        "percent": percent,
        "per_core": per_core,
        "cores": psutil.cpu_count(logical=True),
        "freq_mhz": round(freq.current, 0) if freq else None,
        "temp_c": _get_cpu_temp(),
    }


# --------------------------------------------------------------------------
# GPU (requiere GPUtil, que a su vez requiere nvidia-smi -> solo NVIDIA)
# --------------------------------------------------------------------------
def get_gpu_info():
    gpus = []
    try:
        import GPUtil
        for gpu in GPUtil.getGPUs():
            gpus.append({
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 1),
                "mem_used_mb": round(gpu.memoryUsed, 0),
                "mem_total_mb": round(gpu.memoryTotal, 0),
                "mem_percent": round(gpu.memoryUtil * 100, 1),
                "temp_c": gpu.temperature,
            })
    except Exception:
        # GPUtil no instalado, no hay GPU NVIDIA, o nvidia-smi no disponible
        pass
    return gpus


# --------------------------------------------------------------------------
# ALERTAS
# --------------------------------------------------------------------------
def check_alerts(ram, disk, cpu, gpus):
    alerts = []
    if ram["percent"] >= THRESHOLDS["ram"]:
        alerts.append(f"RAM con uso muy alto: {ram['percent']}%")
    if disk["percent"] >= THRESHOLDS["disk"]:
        alerts.append(f"Disco casi lleno: {disk['percent']}%")
    if cpu["percent"] >= THRESHOLDS["cpu"]:
        alerts.append(f"Procesador con carga muy alta: {cpu['percent']}%")
    for gpu in gpus:
        if gpu["load_percent"] >= THRESHOLDS["gpu"]:
            alerts.append(f"GPU '{gpu['name']}' con carga muy alta: {gpu['load_percent']}%")
    return alerts


def collect_all():
    """Recolecta toda la telemetría en una sola llamada."""
    ram = get_ram_info()
    disk = get_disk_info()
    cpu = get_cpu_info()
    gpus = get_gpu_info()
    alerts = check_alerts(ram, disk, cpu, gpus)
    return {
        "ram": ram,
        "disk": disk,
        "cpu": cpu,
        "gpus": gpus,
        "alerts": alerts,
    }
