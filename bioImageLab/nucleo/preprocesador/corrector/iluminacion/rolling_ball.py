import numpy as np
import warnings
from skimage.restoration import rolling_ball

# Filtro RollingBall

class RollingBall:
    nombre = "rollingBall"
    """
        Es un algoritmo para correccion de fondo : Rueda una esfera por una superficie que define el fondo. Para luego restarlo a la imagen.
        Permite eliminar gradientes suaves, iluminación desigual, y conserva objetos pequeños y brillantes. Depende del Radio, y este debe
        ser mayor al objeto que se quiera conservar.
        -Radio pequeño : Elimina detalles pequeños (Filtrado micro)
        -Radio grande : Elimina fondo suave (Correccion de fondo/iluminación)
    """

    def __init__(self, radio = 50):
        self.radio = _chequear_radio(radio)

    def _chequear_radio(self, radio) -> int: 
        """
            Verifica que el radio, no sea menor a 1.
        """

        if radio < 3:
            warnings.warn(
                f"RollingBall: radio={radio} es muy pequeño. "
                "Se ajusta a 3 píxeles.",
                RuntimeWarning
            )
            return 3
        return int(radio)

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return img - rolling_ball(img, radius = self.radio)