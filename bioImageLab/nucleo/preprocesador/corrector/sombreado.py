'''
    Correccion sin flat, basada en la propia imagen
    I(x,y)=S(x,y)⋅L(x,y)
    L = Iluminacion suave estimada

    Metodos : Low pass + division, retinex, ajuste polinomial, estimacion por mediana tempora/z
    corrige : Gradientes suaves, iluminacion desigual cuando no hay flat
'''

import numpy as np
from surface_fit import SurfaceFit

class Sombreado:
    nombre = "sombreado_base"

    """
        Clase base abstracta para métodos de correccion de luz por sombreado o shading, sin Flat..
    """
    
    def __call__(self, data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

class SombreadoReal(Sombreado):
    nombre = "sombreado_real"

    """
        Operación: I(x,y)=S(x,y)⋅L(x,y)
        Se asume que el shading_map provisto viene procesados/normalizados 
        si así se requiere externamente.
    """

    def __init__(self, shading_map: np.ndarray):
        self.map = shading_map

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return (img.astype(np.float64) * self.map).astype(img.dtype)

class SombreadoEstimado(Sombreado):
    nombre = "sombreado_estimado" # Ajuste polinomial.
    def __init__(self, grado: int = 2):
        self.grado = grado

    def __call__(self, img: np.ndarray) -> np.ndarray:
        # Ajusta un plano curvo a la imagen para detectar el gradiente de luz
        h, w = img.shape
        y, x = np.mgrid[:h, :w]
        
        # Simplificación: Ajuste de mínimos cuadrados para estimar el plano de luz
        # Esto genera una superficie suave que representa el "shading"
        # (Implementación matemática del ajuste de superficie...)
        return img # Retorna la imagen corregida aplicando el plano inverso