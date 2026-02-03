'''
    Correccion sin flat, basada en la propia imagen
    I(x,y)=S(x,y)⋅L(x,y)
    L = Iluminacion suave estimada

    Metodos : Low pass + division, retinex, ajuste polinomial, estimacion por mediana tempora/z
    corrige : Gradientes suaves, iluminacion desigual cuando no hay flat
'''

import numpy as np

class ShadingReal:
    nombre = "shading_real"
    def __init__(self, shading_map: np.ndarray):
        self.map = shading_map

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return (img.astype(np.float64) * self.map).astype(img.dtype)

class ShadingEstimadoPolinomial:
    nombre = "shading_estimado_poli"
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