import cv2
import numpy as np

# Filtro Caja

class CajaBlur:
    nombre = "caja_blur"

    def __init__(self, mascara: tuple[int, int] = (3, 3)):
        """
        Filtro de Caja (Promedio): Suavizado uniforme y rápido.
        
        Argumentos:
            mascara: Tupla (ancho, alto). A diferencia del Gaussiano, 
                     aquí no es obligatorio que sean impares, pero es lo habitual.
        """
        self.mascara = mascara

    def __call__(self, img: np.ndarray) -> np.ndarray:
        """
        Aplica el filtro de promedio (blur) sobre la imagen.
        """
        # cv2.blur es el alias para el filtro de caja normalizado
        return cv2.blur(img, self.mascara)