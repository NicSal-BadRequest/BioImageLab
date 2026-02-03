## Descripción

BioPictureTools es un conjunto de herramientas escritas en Python para procesar y analizar imágenes de microscopía. Permite, entre otras cosas:

    -Detección y rastreo de núcleos
    -Análisis de fluorescencia
    -Manejo de sets de imágenes
    -Versiones compatibles con ambientes locales y Google Colab

## Características

    -Interfaz de línea de comando / scripts fáciles de usar
    -Utiliza bioio y bioio_bioformats para leer formatos comunes de bioimagen
    -Modular: varios scripts para distintos tipos de análisis

## Requisitos

Para poder usar BioPictureTools, necesitas tener:

    -Python 3.x
    -Java (OpenJDK u otra distribución compatible)
    -Dependencias de Python que puedan estar en requirements.txt (o las que los scripts usen)

## Instalación

Aquí los pasos para instalar/configurar el entorno en una PC con Linux (u otro sistema *nix).

```bash
# Ver qué versión de Java está siendo usada o dónde está instalado:
readlink -f $(which java)

# Si usás bash:
nano ~/.bashrc

# O si usás zsh:
nano ~/.zshrc

# Agregar/editar estas líneas en el archivo correspondiente:
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Luego recargar el archivo de configuración:

source ~/.bashrc
# o si usás zsh
source ~/.zshrc

```

Instala las dependencias 

```bash
pip3 install -r requirements.txt
```

## Estructura del proyecto:

```bash
nucleo/
│
├── controlador/
│   └── ControladorBioImagen.py # I/O, metadatos, e iteracion
│
├── preprocesador/
│   ├── normalizador/
│   │   ├── normalizador.py # Handler de la normalizacion : por el metodo y por el corte confocal.
│   │   └── metodosNormalizacion.py # Metodos zscore, max, mim_max, y por percentil.
│   │
│   ├── corrector/
│   │   ├── flat_field.py
│   │   ├── correccion_fondo.py
│   │   └── shading.py
│   │
│   ├── registrador/
│   │   ├── rigid.py
│   │   ├── affine.py
│   │   └── elastic.py
│   │
│   └── correctorArtefactos/
│       ├── hot_pixels.py
│       └── bleaching.py
│
├── filtradores/
│   ├── operadores_locales/                 # dominio espacial
│   │   ├── gaussiano.py
│   │   ├── mediana.py
│   │   ├── cajaBlur.py
│   │   └── bilateral.py
│   │
│   ├── operadores_espectrales/              # dominio frecuencial
│   │   ├── fft_pasabajo.py
│   │   ├── fft_pasaalto.py
│   │   └── fft_pasabanda.py
│   │
│   ├── espacio_escala/                      # multiescala
│   │   ├── dog.py
│   │   ├── log.py
│   │   └── wavelets.py
│
├── realzador/
│   ├── realce_bordes/
│   │   ├── sobel.py
│   │   ├── scharr.py
│   │   └── canny.py
│   │
│   ├── realce_contraste/
│   │   ├── clahe.py
│   │   └── hist_eq.py
│   │
│   ├── morfologia/
│   │   ├── apertura.py
│   │   ├── cierre.py
│   │   ├── top_hat.py
│   │   └── bottom_hat.py
│   │
│   └── mapas_caracteristicas/
│       ├── gradiente.py
│       └── respuesta_filtros.py
│
├── segmentador/
│   ├── binarizacion/
│   │   ├── umbral_global.py
│   │   ├── otsu.py
│   │   ├── adaptativo.py
│   │   └── percentil.py
│   │
│   ├── separacion_instancias/
│   │   ├── watershed.py
│   │   ├── marcadores.py
│   │   └── distancia.py
│   │
│   ├── segmentacion_regiones/
│   │   ├── region_growing.py
│   │   └── superpixeles.py
│   │
│   └── etiquetado/
│       ├── connected_components.py
│       └── label_image.py
│
├── extractor/
│   ├── contornos/
│   │   ├── find_contours.py
│   │   └── hull.py
│   │
│   ├── geometria/
│   │   ├── centroides.py
│   │   ├── bounding_box.py
│   │   ├── area.py
│   │   └── diametro.py
│   │
│   └── relaciones_espaciales/
│       ├── vecinos.py
│       └── colocalizacion.py
│
├── cuantificador/
│   ├── intensidad/
│   │   ├── media.py
│   │   ├── integrada.py
│   │   ├── maximo.py
│   │   └── perfil_lineal.py
│   │
│   ├── morfometria/
│   │   ├── area.py
│   │   ├── perimetro.py
│   │   └── circularidad.py
│   │
│   ├── dinamica_temporal/
│   │   ├── time_series.py
│   │   └── bleaching_curve.py
│   │
│   └── estadisticas_objetos/
│       ├── distribuciones.py
│       └── correlaciones.py
│
├── analizador/
│   ├── plots/
│   │   ├── histogramas.py
│   │   ├── scatter.py
│   │   └── boxplot.py
│   │
│   ├── qc/
│   │   ├── overlays.py
│   │   └── sanity_checks.py
│   │
│   └── exportacion/
│       ├── csv.py
│       ├── parquet.py
│       └── figures.py
│
└── gestorLab/
    ├── pipelinesClasicos/
    │   ├── nuclei_fluorescence.yaml
    │   └── spots_detection.yaml
    │
    ├── personalizados/
    └── validacion/
```

## Ejemplo de uso

```bash
# Ejecutar script principal (supuesto nombre, reemplazá según tu estructura)
python main.py --input ruta/a/las/imagenes --output carpeta_de_salida

# Otro ejemplo para detección de núcleos
python RastreadorNucleos.py --input example.png --threshold 0.2
```

Aquí un ejemplo del resultado generado por BioPictureTools:

![Ejemplo de salida](output/output_example.png)

## Licencia

Este proyecto está bajo la licencia MIT. Para más detalles, revisá el archivo LICENSE.
