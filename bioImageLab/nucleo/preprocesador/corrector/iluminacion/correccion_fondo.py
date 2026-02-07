'''
    Estimacion y sustraccion de fondo aditivo lento.
    I(x,y)=S(x,y)+B(x,y)

    Se puede hacer por filtro gaussiano grande, rolling ball, mediana local o apertura morfologica
    Corrige : 
    Autofluorescencia
    Glow del detector
    Iluminacion ambiental residual

    
'''

import numpy as np
import cv2
from ...realzadores.morfologicos.rolling_ball import RollingBall

class CorreccionFondo:
    nombre = "correccion_fondo"

    """
        Clase base abstracta para métodos de correccion de luz por Correccion de Fondo.
    """
    
    def __call__(self, data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

class CorreccionFondoReal(CorreccionFondo):
    nombre = "correccion_fondo_real"

    """
        Operación: I(x,y)=S(x,y)+B(x,y)
        Se asume que master_dark ya vienen procesados/normalizados 
        si así se requiere externamente.
    """

    def __init__(self, master_dark: np.ndarray):
        self.dark = master_dark

    def __call__(self, img: np.ndarray) -> np.ndarray:
        # Resta con clipping para no tener valores negativos
        return np.maximum(img.astype(np.int32) - self.dark.astype(np.int32), 0).astype(img.dtype)

class CorreccionFondoEstimada(CorreccionFondo):
    nombre = "correccion_fondo_estimada"

    """
        En caso de no haber un campo oscuro de fondo , se puede aproximar usando el algoritmo Rolling Ball.
        Se inyecta un filtrado RollingBall configurado específicamente para estimación de fondo.
        Usando un radio sugerido de 50 px que garantiza que permite conservar objetos lo suficientemente grande, aunque este
        valor haty que ajustarlo.
    """

    def __init__(self, radio: int = 50):
        self.estimador = RollingBall(radio=radio)

    def __call__(self, img: np.ndarray) -> np.ndarray:
        return np.maximum(self.estimador(img).astype(np.float64), 0)