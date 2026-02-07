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
│   └──  corrector/ # Cada uno con dos metodos : el real con imagenes de referencia, y el estimado (usando filtros, realzadores o modelado).
│          ├── iluminacion/
│          │    ├── flat_field.py 
│          │    ├── correccion_fondo.py 
│          │    ├── hot_pixels.py # Esto es mas una correccion de artefactos sencilla sin modelado.
│          │    └── sombreado.py 
│          └── deformaciones/ # Correciones mas complejas usando transformaciones y modelado rigido, afin y elastico. Utilizan modelado.
│              ├── afin.py
│              ├── rigida.py
│              └── elastica.py
│
│
├── filtrador/                 # Su misión es la REDUCCIÓN (Ruido/Fondo)
│   ├── locales/                 # dominio espacial
│   │   ├── gaussiano.py
│   │   ├── mediana.py
│   │   ├── difusionAnisotropica.py
│   │   ├── cajaBlur.py
│   │   └── bilateral.py
│   │
│   ├── espectrales/              # dominio frecuencial
│   │   ├── fft_pasabajo.py
│   │   ├── fft_pasaalto.py
│   │   ├── fft_pasabanda.py
│   │   ├── filtradoNotch.py
│   │   └── fft_pasabanda.py
│   │
│   ├── multiescala/                      # multiescala
│   │   ├── diferenciaGaussiana.py
│   │   ├── diferenciaLaplaciana.py
│   │   ├── piramedesLaplacianas.py
│   │   └── wavelets.py
│   │
│   ├── noLocales/                          # No locales
│          └── nlm.py                          # Non-local medians
│
│
├── realzador/                              # Su misión es la EXPLICITACIÓN (Bordes/Detalle)
│   │
│   ├── contraste/
│   │   ├── clahe.py
│   │   ├── gamma.py
│   │   ├── log.py
│   │   ├── retinex.py
│   │   └── hist_eq.py
│   │
│   ├── deconvolucion/
│   │   ├── wiener.py
│   │
│   ├── morfologicos/
│   │   ├── apertura.py
│   │   ├── cierre.py
│   │   ├── rolling_ball.py
│   │   ├── top_hat.py
│   │   ├── bottom_hat.py
│   │   └── gradienteMorfologico.py
│   │
│   ├── afilacion/
│   │   ├── afilacionLaplaciana.py
│   │   ├── filtroHighBoost.py
│   │   └── mascaraEnforque.py
│   │
│   └── gradientes/
│       ├── hessiano.py
│       ├── laplaciano.py
│       ├── canny.py
│       ├── sobel.py
│       └── scharr.py
│
├── segmentador/
│   ├── binarizacion/
│   │   ├── metodosBinarizacion.py # otsu, global, adaptativo, percentil
│   │   └── binarizador.py
│   │
│   ├── instancial/
│   │   ├── watershed.py
│   │   ├── marcado.py # watershedMarcado
│   │   └── splitDistancial.py
│   │
│   ├── regional/
│   │   ├── region_growing.py
│   │   ├── random_walk.py
│   │   └── superpixel.py
│   │
│   └── etiquetado/
│       ├── connected_components.py
│       └── reetiquetado.py
│
├── transformador/              # Rotaciones, escalado, Warp manual  
│   ├── afin.py
│   ├── rigida.py
│   ├── elastica.py             
│
├── modelador/                 
│   ├── clustering/                 
│   │   ├── pca.py
│   │
│   ├── ajuste/              
│   │   ├── ajuste_superficie.py
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
