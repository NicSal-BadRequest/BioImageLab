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

    def __bool__(self) -> bool:
        # Metodo para indicar si o no está cargada la imagen.
        return self.img is not None

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
    

    def __iter__(self):
        """
        Iterador para poder buscar o iterar para todos los canales por tiempo y por z-stack, 
        obteniendo imágenes bidimensionales para su procesamiento.

        Yields:
            canal, t, z, Tupla (t, z, img_2d) donde img_2d es np.ndarray de forma (Y, X)

        Complejidad:
            O(T*Z*C) iteraciones
        """

        if self.img is None:
            return iter(())
        T, Z, C, _, _ = self.forma
        for canal in range(C):
            for t in range(T):
                for z in range(Z):
                    yield canal, t, z, self.img[t, z, canal].copy()

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


    def __eq__(self, other) -> bool:
        """
            Metodo para comparar dos controladores por tura y por forma. 
            Retorna : Bool
            Complejida : O(1)
        """

        if not isinstance(other, ControladorBioImagen):
            return False

        return (
            self.ruta_imagen == other.ruta_imagen and
            self.forma == other.forma
        )


    def __len__(self) -> int:
        """
            Metodo para determinar la cantidad de fotos totales existentes.
            Retorna : Int
            Complejida : O(1)
        """

        if self.img is None:
            return 0
        T, Z, *_ = self.forma

        return T * Z

    # Metodos para I/O externo : Abrir imagenes, liberar memoria y cachear los bioformatos.
    def __enter__(self):
        self.leer_bioImagen()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.img = None
        self.img_procesada = None

    def __repr__(self) -> str:
        """
            Metodo para debugging.
            Retorna : String
            Complejidad : O(1)
        """
        if self.img is None:
            return f"<ControladorBioImagen ruta='{self.ruta_imagen}' (no cargada)>"

        T, Z, C, Y, X = self.forma

        return (
            f"<ControladorBioImagen "
            f"ruta='{self.ruta_imagen.name}', "
            f"forma=(T={T}, Z={Z}, C={C}, Y={Y}, X={X}), "
            f"canales={self.canales}>"
        )