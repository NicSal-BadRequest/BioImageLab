import cv2
import numpy as np

# Filtro bilateral 

class Bilateral:
    nombre = "bilateral"

    """
        Filtro bilateral que suaviza las texturas internas, pero permite mantener
        los bordes nitidos evitando desparramiento de la señal.
        Nota importante: Se requiere la imagen en forma uint8 o float32.
        Los atributos principales:
        - diam = diametro de la vecinidad (5 para filtro rapido, 9 para offline)
        - sigma_color = Dispersion que a mayor valor, las areas mas distantes se mezclan.
        - sigma_espacio = Dispersion que a mayor valor, pixeles mas lejanos influiran entre si.
    """

    def __init__(self,
                diam : int = 3,
                sigma_color : float = 75, 
                sigma_espacio : float = 75):

        self.diam = diam 
        self.sigma_color = sigma_color
        self.sigma_espacio = sigma_espacio


    def __call__(self, img : np.ndarray) -> np.ndarray:
        """
            Nota importante : Si la imagen no se ha transformado a float32 o uint8 o no es
            de ese formato, y es de tipo uint16, se la transformara temporalmente para poder
            aplicar el filtro.
        """
        es_uint16 = img.dtype == np.uint16 

        if es_uint16:
            return cv2.bilateralFilter(
                img.astype(float32), 
                self.diam, 
                self.sigma_color, 
                self.sigma_espacio
                ).astype(uint16)
        else:
            return cv2.bilateralFilter(
                img, 
                self.diam,
                self.sigma_color, 
                self.sigma_espacio)