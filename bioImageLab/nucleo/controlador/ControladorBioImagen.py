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

TipoOrigen = Union[ImagenEstandar, BioImagen]

class ControladorBioImagen:
    """
    Clase "Handler" para leer y preprocesar imágenes de microscopía en formato .png, .jpg, .tiff y formatos de bioimagen confocal como .ics/.ids.
    Permite :
      - Leer y abrir este tipo de archivos.
      - Preprocesarlos a escala de grises y transformarlos en un MultiArray para "handlear" los diferentes tipos de canales, "z-stacking" y "time-lapse" según el tipo de imagen.
      - Permite transformar las imágenes MultiArray 5D en una estructura indexeable para los 
      tratamientos de operaciones atómicas (formato de solo Y, X) y luego reestructurarlo en 5D.
      - Permite manipular la imagen modificada por operaciones externas para comparar con la original.
    Nota :
      - El MultiArray es [T, Z, C, Y, X] donde T es el "timelapse", Z el "Z-stacking" (diferentes planos en el eje Z), C es el Canal de fluorescencia ("Azul", "Rojo", "Verde" y "Campo" que puede
      ser claro u oscuro), y los ejes de pixeles X e Y son las dimensiones de la imagen.
      - Una imagen bidimensional sería (1, 1, 1, Y, X), por ejemplo, de formatos .jpg y .png.
      - Se usa .copy() en getters y el iterador dado que sino permitiria la sobreescritura en algo que deberia
      ser solo lectura.
    """

    def __init__(self, ruta_imagen):
        self.ruta_imagen = Path(ruta_imagen)
        self.configuracion: TipoOrigen = self._clasificar_imagen(self.ruta_imagen)

        # Datos del MultiArray [T, Z, C, Y, X] pre-procesamiento
        self.img: Optional[np.ndarray] = None
        self.canales: List[str] = []
        self.forma: Tuple[int, ...] = ()

        # Versión del MultiArray post-procesamiento
        self.img_procesada: Optional[np.ndarray] = None

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
                    self.img = img_raw[np.newaxis, np.newaxis, np.newaxis, :, :]
                    self.canales = ["Gris"]

            if self.img is not None:
                self.forma = self.img.shape
                # Inicializar img_procesada con la misma forma
                self.img_procesada = np.zeros_like(self.img)
            return self.img

        except Exception as e:
            print(f"Error al leer la imagen: {e}")
            return None
    
    def iterar_cortes(self, canal: int = 0):
        """
        Iterador para poder buscar o iterar en un canal dado por tiempo y por z-stack, 
        obteniendo imágenes bidimensionales para su procesamiento.

        Argumentos:
            canal: Canal a iterar (default: 0)

        Yields:
            Tupla (t, z, img_2d) donde img_2d es np.ndarray de forma (Y, X)

        Complejidad:
            O(T*Z) iteraciones
        """
        if self.img is None:
            raise ValueError("Imagen no cargada")

        T, Z, C, _, _ = self.forma
        
        if not (0 <= canal < C):
            raise IndexError(f"Canal {canal} fuera de rango. Canales disponibles: 0-{C-1}")

        for t in range(T):
            for z in range(Z):
                yield t, z, self.img[t, z, canal].copy()

    def set_corte_procesado(self,
                            canal: int = 0,
                            t: int = 0,
                            z: int = 0,
                            img_2d: Optional[np.ndarray] = None):
        """
        Método setter para guardar una imagen 2D procesada en la estructura tensor 5D.
        
        Argumentos:
            canal: Índice del canal (default: 0)
            t: Índice del timelapse (default: 0)
            z: Índice del z-stack (default: 0)
            img_2d: Objeto np.ndarray a settear (si None, crea array de ceros)

        Complejidad:
            O(1)
        """
        if self.img_procesada is None:
            raise ValueError("img_procesada no inicializada")

        T, Z, C, Y, X = self.forma
        
        if not (0 <= t < T and 0 <= z < Z and 0 <= canal < C):
            raise IndexError(f"Índices fuera de rango. T max: {T-1}, Z max: {Z-1}, C max: {C-1}")

        if img_2d is None:
            img_2d = np.zeros((Y, X), dtype=self.img.dtype)

        assert img_2d.ndim == 2, "img_2d debe ser 2D con forma (Y, X)"
        assert img_2d.shape == (Y, X), f"img_2d debe tener forma ({Y}, {X}), tiene {img_2d.shape}"
        
        self.img_procesada[t, z, canal] = img_2d
    
    def _get_corte(self, 
                   img: np.ndarray, 
                   canal: int,
                   t: int,
                   z: int) -> np.ndarray:
        """
        Función interna para realizar cortes en alguna estructura imagen 5D.
        
        Argumentos:
            img: Array 5D [T, Z, C, Y, X]
            canal: Índice del canal
            t: Índice del timelapse
            z: Índice del z-stack

        Retorna:
            Array 2D [Y, X]

        Complejidad:
            O(1) - solo indexación y copia
        """
        T, Z, C, _, _ = img.shape
        
        if not (0 <= t < T and 0 <= z < Z and 0 <= canal < C):
            raise IndexError(f"Índices fuera de rango. T max: {T-1}, Z max: {Z-1}, C max: {C-1}")
        
        return img[t, z, canal].copy()

    def get_corte_original(self,
                           canal: int = 0,
                           t: int = 0,
                           z: int = 0) -> np.ndarray:
        """
        Método getter para obtener un corte de la estructura tensor 5D original.
        
        Argumentos:
            canal: Índice del canal (default: 0)
            t: Índice del timelapse (default: 0)
            z: Índice del z-stack (default: 0)

        Retorna:
            Imagen 2D np.ndarray de forma (Y, X)

        Complejidad:
            O(1)
        """
        if self.img is None:
            raise ValueError("Imagen original no cargada")

        return self._get_corte(self.img, canal, t, z)

    def get_corte_procesado(self,
                            canal: int = 0,
                            t: int = 0,
                            z: int = 0) -> np.ndarray:
        """
        Método getter para obtener un corte de la estructura tensor 5D procesada.
        
        Argumentos:
            canal: Índice del canal (default: 0)
            t: Índice del timelapse (default: 0)
            z: Índice del z-stack (default: 0)

        Retorna:
            Imagen 2D np.ndarray de forma (Y, X)

        Complejidad:
            O(1)
        """
        if self.img_procesada is None:
            raise ValueError("No se ha hecho ninguna operación de procesamiento")

        return self._get_corte(self.img_procesada, canal, t, z)

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
            T, Z, C, Y, X = self.forma

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