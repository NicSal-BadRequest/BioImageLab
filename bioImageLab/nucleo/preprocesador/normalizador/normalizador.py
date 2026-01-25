import numpy as np
from metodosNormalizacion import (
    MetodoNormalizacion, 
    MaxNorm, 
    MinMaxNorm, 
    PercentilNorm, 
    ZScoreNorm
)
from dataclasses import dataclass
from typing import Union, List, Optional

# Tipos inmutables para manejar formas de normalización

@dataclass(frozen=True) 
class Norm_Global:
    """Normaliza todas las imágenes de un canal por el máximo encontrado en todo el canal."""
    pass

@dataclass(frozen=True)
class Z_Norm_PorCorte:
    """Normaliza cada corte Z según su propio máximo interno en dicho corte."""
    pass

@dataclass(frozen=True)
class T_Norm_PorCorte:
    """
    Normaliza cada fotograma según su propio máximo en dicho fotograma.
    El máximo de un fotograma afecta a todos los cortes Z.
    """
    pass

TipoNormalizacion = Union[Norm_Global, Z_Norm_PorCorte, T_Norm_PorCorte]


class Normalizador:
    """
    Clase para gestionar los diferentes tipos de normalización en imágenes confocales y aplicar 
    diferentes métodos de normalización.
    
    Nota: 
        - img_normalizada[i] corresponde al canal i original, con forma (T, Z, 1, Y, X). 
        - Los canales no procesados permanecen como None.
    
    Ejemplo de uso:
        >>> norm = Normalizador(tipo=Norm_Global(), metodo=MaxNorm())
        >>> img_norm = norm(img_5d, canal=0)
    """
    nombre = "normalizador"
    
    def __init__(
        self, 
        tipo: TipoNormalizacion = Norm_Global(),
        metodo: MetodoNormalizacion = MaxNorm()
    ):
        """
        Args:
            tipo: Estrategia de normalización (Global, por Z, por T)
            metodo: Algoritmo de normalización (MaxNorm, MinMaxNorm, etc.)
        """
        self.tipo = tipo
        self.metodo = metodo 
        self.img_normalizada: Optional[List[Optional[np.ndarray]]] = None

    def __call__(
        self,
        img_5d: np.ndarray,
        canal: int = 0,
        z_ref: int = 0,
        t_ref: int = 0,
    ) -> np.ndarray:
        """
        Normaliza un canal independientemente según el tipo y método especificado.
        Cada fluoróforo tiene su propia intensidad máxima, por lo que se normaliza canal por canal.

        Argumentos:
            img_5d: Array 5D con forma [T, Z, C, Y, X]
            canal: Índice del canal a normalizar (default: 0)
            z_ref: Z-stack de referencia (no usado en esta versión) (default: 0)
            t_ref: Timelapse de referencia (no usado en esta versión) (default: 0)

        Retorno:
            Array 5D normalizado [T, Z, 1, Y, X] del canal

        Complejidad:
            O(T*Z*Y*X) en el peor caso
        """
        if img_5d.ndim != 5:
            raise ValueError(f"img_5d debe ser 5D [T, Z, C, Y, X], tiene {img_5d.ndim} dimensiones")
        
        T, Z, C, Y, X = img_5d.shape
        
        if not (0 <= canal < C):
            raise IndexError(f"Canal {canal} fuera de rango. Canales disponibles: 0-{C-1}")
        if not (0 <= t_ref < T):
            raise IndexError(f"t_ref={t_ref} fuera de rango. T max: {T-1}")
        if not (0 <= z_ref < Z):
            raise IndexError(f"z_ref={z_ref} fuera de rango. Z max: {Z-1}")

        try:
            # Convertir a float para evitar pérdida de precisión
            img_float = img_5d.astype(np.float64)

            # Inicializar lista de canales normalizados si no existe
            if self.img_normalizada is None:
                self.img_normalizada = [None for _ in range(C)]

            # Inicializar el canal específico si no existe
            if self.img_normalizada[canal] is None:
                self.img_normalizada[canal] = np.zeros((T, Z, 1, Y, X), dtype=np.float64)

            match self.tipo:
                case Norm_Global():
                    # Extraer datos del canal a normalizar
                    canal_data = img_float[:, :, canal, :, :]
                    # Aplicar método de normalización
                    self.img_normalizada[canal][:, :, 0, :, :] = self.metodo(canal_data)
                    print(f"Canal {canal} normalizado globalmente con {self.metodo.nombre}")

                case Z_Norm_PorCorte():
                    # Normalizar cada corte Z independientemente
                    for z in range(Z):
                        canal_data = img_float[:, z, canal, :, :]
                        self.img_normalizada[canal][:, z, 0, :, :] = self.metodo(canal_data)
                    print(f"Canal {canal}: {Z} cortes Z normalizados con {self.metodo.nombre}")

                case T_Norm_PorCorte():
                    # Normalizar cada fotograma independientemente
                    for t in range(T):
                        canal_data = img_float[t, :, canal, :, :]
                        self.img_normalizada[canal][t, :, 0, :, :] = self.metodo(canal_data)
                    print(f"Canal {canal}: {T} fotogramas normalizados con {self.metodo.nombre}")

            return self.img_normalizada[canal]

        except Exception as e:
            print(f"Error al normalizar la imagen: {e}")
            import traceback
            traceback.print_exc()
            return None

    def reset(self):
        """Resetea las imágenes normalizadas almacenadas."""
        self.img_normalizada = None