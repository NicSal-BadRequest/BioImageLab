import cv2
import numpy as np
import warnings

# Filtro mediana

class Mediana:
    nombre = "mediana"

    """
        Filtro mediana para eliminar ruido tipo 'sal y pimienta' (pixeles muy saturados o muertos),
        preserva mejor los bordes.
    """

    def __init__(self,
                mascara: int = 3):
        self.mascara = mascara
    
    def _chequear_mascara(self, mascara : int) -> int:
        """
            Verifica si la mascara es adecuada para su aplicacion en el filtro.
            El valor debe de ser impar. En caso de no ser, se modifica el valor par 
            a uno impar.

            Argumento : Mascara (int) de la mediana.
            Retorna : int. Mismo valor o modificado para que sea impar.
        """
        self.mascara = mascara if mascara % 2 != 0 else mascara + 1
        if self.mascara != mascara:
            warnings.warn(
                f"Nota: Mediana corregida a {self.mascara}.",
                RuntimeWarning
            )

    def __call__(self, img : np.ndarray) -> np.ndarray:
        return cv2.medianBlur(img, self.mascara)
