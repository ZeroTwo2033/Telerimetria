# GameHW Monitor

Programa de escritorio en Python con interfaz gráfica (Tkinter) para revisar en
tiempo real el rendimiento de los componentes del equipo mientras se juega:
RAM, disco duro, procesador (uso y temperatura) y tarjeta gráfica (uso, VRAM
y temperatura), con alertas automáticas cuando el uso es muy alto.

## Estructura del proyecto

```
game_monitor/
├── main.py               # Punto de entrada
├── gui.py                 # Interfaz gráfica (Tkinter, tema neón morado)
├── hardware_monitor.py     # Recolección de datos de hardware y alertas
├── requirements.txt
└── README.md
```

## Instalación

```bash
cd game_monitor
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Funcionalidad

- **Resumen general**: barras de uso de RAM, disco, CPU y GPU en una sola pantalla.
- **RAM**: total, usada, disponible y porcentaje de uso.
- **Disco**: espacio total, usado, libre y porcentaje.
- **Procesador**: uso general, uso por núcleo, frecuencia y temperatura (si el
  sistema la expone).
- **Tarjeta gráfica**: nombre, uso (%), VRAM usada/total y temperatura
  (solo GPU NVIDIA, vía `GPUtil`/`nvidia-smi`).
- **Alertas**: si algún componente supera su umbral (editable en
  `hardware_monitor.py -> THRESHOLDS`, por defecto 85-90%), se muestra un
  aviso en rojo en la parte superior de la ventana.

Los botones de la barra superior permiten alternar entre el resumen general
y la vista detallada de cada componente.

## Limitaciones importantes (léelas antes de usar)

- **Temperatura de CPU**: en Linux normalmente funciona sin configuración
  adicional (usa `psutil.sensors_temperatures()`). En **Windows**, `psutil`
  no expone temperaturas de forma nativa; este programa intenta leerlas vía
  `OpenHardwareMonitor` + WMI. Para que funcione:
  1. Descarga e instala [OpenHardwareMonitor](https://openhardwaremonitor.org/).
  2. Ejecútalo (debe quedar corriendo en segundo plano) como administrador.
  3. Instala el paquete opcional `wmi` (`pip install wmi pywin32`).
  Si no se cumple esto, la app mostrará "No disponible en este sistema" en
  vez de fallar.
- **GPU**: la detección de uso/temperatura de tarjeta gráfica solo funciona
  con **GPU NVIDIA** que tenga instalado `nvidia-smi` (viene con los
  drivers oficiales). Tarjetas AMD o Intel no son soportadas por `GPUtil`;
  en ese caso la vista de GPU mostrará un aviso indicándolo.
- El programa está pensado para Windows/Linux con Python 3.9+.

## Convertirlo en una aplicación de doble clic

Ya no necesitas usar la terminal cada vez. Compílalo **una sola vez** en cada
computadora y quedará un ícono para siempre.

### En Windows
1. Doble clic en `build_windows.bat`.
2. Espera a que termine (instala dependencias y compila).
3. Copia el archivo `dist\GameHWMonitor.exe` a tu Escritorio.
4. Desde ahora, doble clic en ese `.exe` abre la app directamente.

### En Ubuntu
1. Abre una terminal **una sola vez** dentro de la carpeta del proyecto y
   ejecuta:
   ```bash
   bash instalar_ubuntu.sh
   ```
2. Esto compila la app y crea automáticamente un ícono `GameHWMonitor.desktop`
   en tu Escritorio.
3. Si al hacer doble clic te pide confirmar, haz clic derecho sobre el ícono
   y elige "Permitir ejecución" o "Confiar y lanzar" (depende de tu versión
   de Ubuntu), y luego doble clic normal.
4. Desde ahí en adelante, doble clic en el ícono abre la app sin terminal.

> Nota: el ejecutable generado es exclusivo del sistema operativo donde lo
> compilaste (el `.exe` solo sirve en Windows, el binario de Ubuntu solo en
> Linux). Si usas la app en ambas computadoras, corre el script
> correspondiente en cada una.

## Personalización rápida

- Colores del tema: al inicio de `gui.py` (`NEON_PURPLE`, `COLOR_TOP`,
  `COLOR_BOTTOM`, etc.).
- Umbrales de alerta: diccionario `THRESHOLDS` en `hardware_monitor.py`.
- Frecuencia de actualización: constante `REFRESH_MS` en `gui.py`
  (milisegundos, por defecto 1500).
