'''
    Tipo de Correcion de iluminacion para las variaciones espaciales multiplicativas del
    sistema optico.

    I_corr(x,y) = [I(x,y) - D(x,y)] / [F(x,y) - D(x,y)]
    F = Campo plano (flat)
    D = Dark current (opcinal)

    Corrige:
        - vineteo
        - desigual sensibilidad del sensor
        - iluminacion no uniforme del campo
        - requiere referencia
'''

import numpy as np
import cv2
from ...filtradores.operadoresLocales.gaussiano import Gaussiano

class FlatField:
    nombre = "base_flat_field"

    """
        Clase base abstracta para métodos de correccion de luz por Flat Field.
    """
    
    def __call__(self, data: np.ndarray) -> np.ndarray:
        raise NotImplementedError

class FlatFieldReal(FlatField):
    nombre = "flat_field_real"
    
    def __init__(self, master_flat: np.ndarray, master_dark: np.ndarray = None):
        """
            Operación: (I - D) / (F - D)
            Se asume que master_flat y master_dark ya vienen procesados/normalizados 
            si así se requiere externamente.
        """
        self.F = master_flat.astype(np.float64)
        self.D = master_dark.astype(np.float64) if master_dark is not None else 0.0

    def __call__(self, img: np.ndarray) -> np.ndarray:
        # Operación atómica pura
        img_flat = img.astype(np.float64)
        denominador = self.F - self.D
        
        # Manejo de división por cero funcional: devolver identidad donde el denominador sea 0
        return np.where(denominador > 0, (img_flat - self.D) / denominador, img_flat)

class FlatFieldEstimado:
    nombre = "flat_field_estimado"
    
    def __init__(self, sigma: float = 100.0, mascara: tuple[int, int] = (0, 0)):
        """
            En caso de no haber un campo plano de fondo y otra oscura, se puede aproximar usando una correccion gaussiana.
            Se inyecta un filtrado Gaussiano configurado específicamente para estimación de fondo.
            Un sigma alto (100) garantiza que solo se capture la curvatura de la luz, con una mascara pequeña : Evitar que tome objetos pequeños, 
            no puntuales como luz erronea o como fondo.
        """
        # Instanciamos el Gaussiano internamente con los parámetros de "fondo"
        self.estimador = Gaussiano(sigma=sigma, mascara=mascara)

    def __call__(self, img: np.ndarray) -> np.ndarray:
        # F_estimado captura la tendencia global de iluminación (el viñeteo)
        F_estimado = self.estimador(img).astype(np.float64)
        img_flat = img.astype(np.float64)
        
        # Para la corrección multiplicativa pura I / F
        # np.where maneja la división por cero de forma vectorial
        return np.where(F_estimado > 0, img_flat / F_estimado, img_flat)