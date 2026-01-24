import numpy as np
import cv2
from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Optional, Tuple
from bioio import BioImage
import bioio_bioformats
import matplotlib.pyplot as plt

# Tipos inmutables para manejar archivos

@dataclass(frozen=True)
class ImagenEstandar:
    ruta: Path

@dataclass(frozen=True)
class BioImagen:
    ruta: Path

# Tipo inmutables para manejar formas de normalizacion

TipoOrigen = Union[ImagenEstandar, BioImagen]

# Normaliza a todas las imagenes de un canal por el maximo encontrado en algun corte
@dataclass(frozen=True) 
class Norm_Global:
  pass

# Normaliza a todos los cortes Z de un cana dado la referencia pasada especifica o corte especifico
@dataclass(frozen=True) 
class Z_Norm_Global:
  z_stack: int

# Normaliza cada corte Z segun su propio maximo interno en dicho corte
@dataclass(frozen=True)
class Z_Norm_PorCorte:
  pass

# Normaliza cada fotograma segun uno pasado por referencia o fotograma especifico.
@dataclass(frozen=True)
class T_Norm_Global:
  imelapse: int

# Normaliza cada fotograma segun su propio maximo en dicho fotograma
# El maximo de un fotograma afecta a todos los cortes Z, es un como un global para los Z y canales de dicho fotograma.
@dataclass(frozen=True)
class T_Norm_PorCorte:
  pass

# Clase Handler central para la decodificacion y normalizacion

class ControladorBioImagen:
    """
    Clase "Handler" para leer y procesar imagenes de microscopía en formato .png, .jpg, .tiff y formatos de bioimagen confocal como .ics/.ids.
    Permite :
      - Leer y abrir este tipo de archivos
      - Procesarlos a escala de grises y transformarlos en un MultiArray para "handlear" los diferentes tipos de canales, "z-stacking" y "time-lapse" según el tipo de imagen.
      - Binarizar la imagen y segmentar objetos.
      - Detectar y extraer características de objetos : Centroides y posiciones en la imagen de los mismos.
    Nota :
      - El MultiArray es [T, Z, C, Y, X] donde T es el "timelapse", Z el "Z-stacking" (diferentes planos en el eje Z), C es el Canal de fluorescencia ("Azul", "Rojo", "Verde" y "Campo" que puede
      ser claro u oscuro), y los ejes de pixeles X e Y son las dimensiones de la imagen.
      - Una imagen bidimensional seria (1, 1, 1, Y, X), por ejemplo, de formatos .jpg y .png.
      - img_normalizada[i] corresponde al canal i original, con forma (T, Z, 1, Y, X). Los canales no procesados
       permanecen como None. Lo mismo ocurre para img_binaria[i].
    """

    def __init__(self, ruta_imagen):
        self.ruta_imagen = Path(ruta_imagen)
        self.configuracion: TipoOrigen = self._clasificar_imagen(self.ruta_imagen)

        # Datos del MultiArray [T, Z, C, Y, X] pre-procesamiento
        self.img: Optional[np.ndarray] = None
        self.canales: List[str] = []
        self.forma: Tuple[int, ...] = ()

        # Version del MultiArray post-procesamiento :
        self.img_normalizada: Optional[List[np.ndarray]] = None #Que sea un array donde contenga cada canal normalizado si se quiere.
        self.img_binaria: Optional[List[np.ndarray]] = None # Idem de lo anterior


    def _clasificar_imagen(self, ruta: Path) -> TipoOrigen:
        """
          Determina el tipo de origen basado en la extensión (Fábrica).
        """
        formatos_bio = {".ids", ".ics", ".tiff", ".tif"}
        if ruta.suffix.lower() in formatos_bio:
            return BioImagen(ruta)
        return ImagenEstandar(ruta)

    def leer_bioImagen(self) -> Optional[np.ndarray]:
        """
          Selector de modos estricto para cargar y normalizar a 5D.
        """
        try:
            match self.configuracion:
                case BioImagen(ruta):
                    img = BioImage(ruta, reader=bioio_bioformats.Reader)
                    self.img = img.get_image_data("TZCYX")
                    self.canales = img.channel_names

                case ImagenEstandar(ruta):
                    img_raw = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
                    if img_raw is None:
                        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

                    # Normalización a 16-bit y expansión a 5D: [T, Z, C, Y, X]
                    img_raw = img_raw.astype(np.uint16) * 256
                    self.img = img_raw[np.newaxis, np.newaxis, np.newaxis, :, :] # Agregar los datos faltantes de las primeras componentes
                    self.canales = ["Gris"]

            if self.img is not None:
                self.forma = self.img.shape
            return self.img

        except Exception as e:
            print(f"Error al leer la imagen: {e}")
            return None

    def normalizar_bioImagen(self,
                             canal: int = 0,
                             z_ref : int = 0,
                             t_ref: int = 0,
                             modo: ModoNormalizacion = Norm_Global()
                             ) -> Optional[np.ndarray]:
        """
        Normaliza cada canal independientemente al rango [0, 1] dividiendo por su valor máximo.
        Cada fluoróforo tiene su propia intensidad máxima, por lo que se normaliza canal por canal.

        Retorno:
            Array 5D normalizado [T, Z, C, Y, X] o None si hay error
        Coste:
            O(T*Z*Y*X)
        """
        if self.img is None:
            print("Error: Primero debes cargar la imagen con leer_bioImagen()")
            return None

        try:
            T, Z, C, Y, X = self.img.shape

            # Verificar que el canal existe
            if canal >= C or canal < 0:
                print(f"Error: Canal {canal} no existe. Canales disponibles: 0-{C-1}")
                print(f"Nombres de canales: {self.canales}")
                return None

            if t_ref >= T or z_ref >= Z:
                print(f"Error: Índices fuera de rango. T max: {T-1}, Z max: {Z-1}")
                return None

            # Convertir a float para evitar pérdida de precisión
            img_float = self.img.astype(np.float64)

            # Inicializar lista de arrays normalizados si no existe
            if self.img_normalizada is None:
                # Lista de C elementos, cada uno es un array 5D inicializado en ceros
                self.img_normalizada = [np.zeros((T, Z, 1, Y, X), dtype=np.float64) for _ in range(C)]

            match modo:
                case Norm_Global():
                  # Extraer datos del canal a normalizar
                  canal_data = img_float[:, :, canal, :, :]
                  canal_max = canal_data.max()

                  if canal_max == 0:
                    print(f"Advertencia: Canal {canal} ({self.canales[canal]}) tiene valor máximo 0")
                    # Guardar el canal sin normalizar en la posición de la lista
                    self.img_normalizada[canal][:, :, 0, :, :] = canal_data
                  else:
                    # Normalizar el canal y guardarlo
                    self.img_normalizada[canal][:, :, 0, :, :] = canal_data / canal_max
                    print(f"Canal {canal} ({self.canales[canal]}): max={canal_max:.2f}, normalizado a [0, 1]")

                case Z_Norm_Global():
                  # Extraer los datos del z_stack de interes por el que se normalizara todo el canal:
                  canal_data = img_float[:, z_ref, canal, :, :]
                  z_ref_max = canal_data.max()
                  if z_ref_max == 0:
                    print(f"Advertencia: Z-stack {z_ref} ({self.canales[canal]}) tiene valor máximo 0")
                    self.img_normalizada[canal][:, :, 0, :, :] = canal_data
                  else:
                    self.img_normalizada[canal][:, :, 0, :, :] = canal_data / z_ref_max
                    print(f"Z-stack {z_ref} ({self.canales[canal]}): max={z_ref:.2f}, normalizado a [0, 1]")

                case Z_Norm_PorCorte():
                  # Extraer los datos de todos los cortes Z del canal y normalizar por corte segun maximo interno:
                  for z in range(Z):
                    canal_data = img_float[:, z, canal, :, :]
                    z_max = canal_data.max()
                    if z_max == 0:
                      print(f"Advertencia: Z-stack {z} ({self.canales[canal]}) tiene valor máximo 0")
                      self.img_normalizada[canal][:, z, 0, :, :] = canal_data
                    else:
                      self.img_normalizada[canal][:, z, 0, :, :] = canal_data / z_max
                      print(f"Z-stack {z} ({self.canales[canal]}): max={z_max:.2f}, normalizado a [0, 1]")

                case T_Norm_Global():
                  # Extraer los datos de todos los cortes por un canal dado en todos su fotogramas para normalizar por
                  # aquel fotograma con mayor maximo pasado por parametro.
                  canal_data = img_float[t_ref, :, canal, :, :]
                  t_ref_max = canal_data.max()
                  if t_ref_max == 0:
                    print(f"Advertencia: Fotograma {t_ref} ({self.canales[canal]}) tiene valor máximo 0")
                    self.img_normalizada[canal][t_ref, :, 0, :, :] = canal_data
                  else:
                    self.img_normalizada[canal][t_ref, :, 0, :, :] = canal_data / t_ref_max
                    print(f"Fotograma {t_ref} ({self.canales[canal]}): max={t_ref_max:.2f}, normalizado a [0, 1]")

                case T_Norm_PorCorte():
                  # Extraer los datos de todos los cortes por un canal dado en todos su fotogramas para normalizar
                  # por el maximo encontrado en cada fotograma.
                  for t in range(T):
                    canal_data = img_float[t, :, canal, :, :]
                    t_max = canal_data.max()
                    if t_max == 0:
                      print(f"Advertencia: Fotograma {t} ({self.canales[canal]}) tiene valor máximo 0")
                      self.img_normalizada[canal][t, :, 0, :, :] = canal_data
                    else:
                      self.img_normalizada[canal][t, :, 0, :, :] = canal_data / t_max
                      print(f"Fotograma {t} ({self.canales[canal]}): max={t_max:.2f}, normalizado a [0, 1]")

            return self.img_normalizada[canal]

        except Exception as e:
            print(f"Error al normalizar la imagen: {e}")
            return None

    def binarizar_bioImagen(self, umbral: float = 0.5, canal: int = 0) -> Optional[np.ndarray]:
        """
        Binariza un canal específico de la imagen normalizada según un umbral.
        Procesa todos los timeframes (T) y z-stacks (Z) del canal seleccionado.

        Argumentos:
            umbral: Valor de umbral para binarización [0.0 - 1.0] (default: 0.5)
            canal: Índice del canal a binarizar (default: 0)

        Retornos:
            Array 5D binarizado [T, Z, C, Y, X] o None si hay error
        Coste:
            O(T*Z*X*Y) operaciones por pixel por Z-stack y timelapse.
        """
        if self.img_normalizada is None:
            print("Error: Primero debes normalizar la imagen con normalizar_bioImagen()")
            return None

        try:
            T, Z, _, Y, X = self.img_normalizada[canal].shape
            C = len(self.canales)

            # Verificar que el canal existe
            if canal >= C or canal < 0:
                print(f"Error: Canal {canal} no existe. Canales disponibles: 0-{C-1}")
                print(f"Nombres de canales: {self.canales}")
                return None

            # Inicializar lista de arrays binarios si no existe
            if self.img_binaria is None:
                self.img_binaria = [np.zeros((T, Z, 1, Y, X), dtype=np.uint8) for _ in range(C)]

            # Binarizar cada timeframe y z-stack del canal seleccionado

            """
            # Forma menos eficiente.
            for t in range(T):
                for z in range(Z):
                    # Extraer el corte 2D del canal
                    corte_2d = self.img_normalizada[canal][t, z, 0, :, :]

                    # Aplicar umbral (operación vectorizada)
                    corte_binario = np.zeros_like(corte_2d, dtype=np.uint8)
                    corte_binario[corte_2d > umbral] = 1
                    corte_binario[corte_2d <= umbral] = 0

                    # Guardar en el array binarizado (escalar a 0-255)
                    self.img_binaria[canal][t, z, 0, :, :] = (corte_binario * 255).astype(np.uint8)
            """

            # Binarización vectorizada - Todo el array de una vez : Se ejecuta todo en C por Numpy.
            # Aplicar umbral a todo el tensor [T, Z, 1, Y, X]
            corte_binario = (self.img_normalizada[canal] > umbral).astype(np.uint8)

            # Escalar a 0-255 (vectorizado)
            self.img_binaria[canal] = (corte_binario * 255).astype(np.uint8)

            return self.img_binaria[canal]

        except Exception as e:
            print(f"Error al binarizar la imagen: {e}")
            return None

    def plot_bioImagen_jn(self, canal: int = 0, z_stack: int = 0, timelapse: int = 0, fluoroforo: str = None):
        """
          Visualización avanzada de BioImágenes con estilos Retro (fluoróforos) o Profesional (Trans).

          Argumentos:
              canal: Canal a visualizar (default: 0)
              z_stack: Índice del z-stack (default: 0)
              timelapse: Índice del timelapse (default: 0)
              fluoroforo: Tipo de fluoróforo ('gfp', 'rfp', 'yfp', 'mcherry', 'dsred',
                        'cerulean_venus', 'cy5', 'dapi', 'fitc', 'mng').
                        Si es None, usa estilo Profesional (Trans).

          Retorna:
              None si hay error

          Complejidad:
              O(1) - solo extrae y muestra slices específicos
        """
        if self.img is None:
            print("Error: Primero debes cargar la imagen con leer_bioImagen()")
            return None

        try:
            T, Z, C, Y, X = self.img.shape

            # Validación de índices
            if canal >= C or canal < 0:
                print(f"Error: Canal {canal} no existe. Disponibles: 0-{C-1}")
                print(f"Nombres de canales: {self.canales}")
                return None
            if timelapse >= T or z_stack >= Z:
                print(f"Error: Índices fuera de rango. T max: {T-1}, Z max: {Z-1}")
                return None

            # Extraer corte de imagen original
            corte_imagen = self.img[timelapse, z_stack, canal, :, :]

            # --- MAPA DE COLORES PARA FLUORÓFOROS (RETRO) ---
            mapa_fluoroforos = {
                'gfp': 'Greens', 'fitc': 'Greens', 'mng': 'Greens',
                'rfp': 'Reds', 'mcherry': 'Reds', 'dsred': 'Reds',
                'yfp': 'YlOrBr',  # Amarillo brillante
                'dapi': 'Blues', 'cerulean_venus': 'GnBu',
                'cy5': 'Purples'
            }

            # Determinar estilo
            es_retro = False
            target_cmap = 'magma'  # Por defecto para modo Profesional

            if fluoroforo and fluoroforo.lower() in mapa_fluoroforos:
                target_cmap = mapa_fluoroforos[fluoroforo.lower()]
                es_retro = True

            # Verificar si hay imagen binarizada
            tiene_binaria = (self.img_normalizada is not None and
                            self.img_binaria is not None and
                            canal < len(self.img_binaria) and
                            self.img_binaria[canal] is not None)

            # --- CONFIGURACIÓN DE ESTILO ---
            accent_color = '#33FF33' if es_retro else 'white'
            face_color = 'black' if es_retro else '#0a0a0a'
            font_style = 'monospace' if es_retro else 'sans-serif'

            # Crear figura con contexto de estilo
            plt.style.use('dark_background')
            num_plots = 2 if tiene_binaria else 1
            fig, axes = plt.subplots(1, num_plots,
                                    figsize=(15 if tiene_binaria else 8, 7),
                                    facecolor=face_color)

            # Convertir axes a lista si solo hay un plot
            if not tiene_binaria:
                axes = [axes]

            # --- PLOT 1: IMAGEN ORIGINAL ---
            if es_retro:
                # Invertir la imagen: fondo oscuro → negro, señales altas → blancas
                corte_invertido = corte_imagen.max() - corte_imagen
                # Aplicar colormap del fluoróforo (ahora sobre imagen invertida)
                cmap = plt.colormaps.get_cmap(target_cmap).copy()
                im0 = axes[0].imshow(corte_invertido, cmap=cmap, interpolation='bilinear')
                axes[0].set_facecolor('black')  # Fondo negro
            else:
                im0 = axes[0].imshow(corte_imagen, cmap=target_cmap)

            if es_retro:
                titulo_0 = f">> {fluoroforo.upper()}_SIGNAL"
                axes[0].set_title(titulo_0, color=accent_color, fontsize=12,
                                 loc='left', pad=15, fontfamily='monospace')
                axes[0].grid(color=accent_color, linestyle=':', alpha=0.3)
                for spine in axes[0].spines.values():
                    spine.set_color(accent_color)
                    spine.set_linewidth(1.5)
                axes[0].tick_params(colors=accent_color, labelsize=8)
            else:
                titulo_0 = f"Canal: {self.canales[canal]}"
                axes[0].set_title(titulo_0, color=accent_color, fontsize=12, pad=15)
                axes[0].axis('off')
                plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04,
                           label='Intensidad')

            # --- PLOT 2: IMAGEN BINARIA (si existe) ---
            if tiene_binaria:
                corte_bin = self.img_binaria[canal][timelapse, z_stack, 0, :, :]

                if es_retro:
                    # En modo retro: invertir binaria y aplicar color del fluoróforo
                    # 0 → 255 (blanco→color), 255 → 0 (negro)
                    corte_bin_invertido = 255 - corte_bin
                    cmap_bin = plt.colormaps.get_cmap(target_cmap).copy()
                    axes[1].imshow(corte_bin_invertido, cmap=cmap_bin, interpolation='nearest')
                    axes[1].set_facecolor('black')  # Fondo negro
                else:
                    # En modo Trans: objetos blancos sobre fondo negro
                    axes[1].imshow(corte_bin, cmap='gray_r')
                    axes[1].set_facecolor('black')

                if es_retro:
                    axes[1].set_title(">> BINARY_DECODE", color=accent_color,
                                    fontsize=12, loc='left', pad=15,
                                    fontfamily='monospace')
                    axes[1].grid(color=accent_color, linestyle=':', alpha=0.3)
                    for spine in axes[1].spines.values():
                        spine.set_color(accent_color)
                        spine.set_linewidth(1.5)
                    axes[1].tick_params(colors=accent_color, labelsize=8)
                else:
                    axes[1].set_title("Binaria", color=accent_color,
                                    fontsize=12, pad=15)
                    axes[1].axis('off')

            # Título superior
            suptitle_text = f"Z:{z_stack} | T:{timelapse} | BIO-IMAGING SYSTEM" if es_retro else f"Canal {canal} | Z-stack:{z_stack} | Tiempo:{timelapse}"
            plt.suptitle(suptitle_text, color=accent_color, fontsize=10,
                        alpha=0.7, y=0.98, fontfamily=font_style)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error al graficar la imagen: {e}")
            import traceback
            traceback.print_exc()
            return None