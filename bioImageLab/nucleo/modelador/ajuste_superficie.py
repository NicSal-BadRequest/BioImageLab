import numpy as np
from itertools import combinations_with_replacement


class AjusteSuperficie:
    """
        Estimador de fondo mediante ajuste polinómico 2D.

        Ajusta una superficie polinómica de grado arbitrario
        a una imagen usando mínimos cuadrados.
    """

    nombre = "ajuste_superficie"

    def __init__(self, grado: int = 2):
        if grado < 0:
            raise ValueError("El grado del polinomio debe ser >= 0")
        self.grado = grado

    def __call__(self, img: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
        """
        Estima el fondo de la imagen.

        Parameters
        ----------
        img : np.ndarray
            Imagen 2D (float recomendado).
        mask : np.ndarray, optional
            Máscara booleana donde True indica píxeles
            a usar para el ajuste.

        Returns
        -------
        fondo : np.ndarray
            Superficie polinómica ajustada.
        """
        h, w = img.shape
        y, x = np.mgrid[:h, :w]

        x = x.ravel()
        y = y.ravel()
        z = img.ravel()

        if mask is not None:
            mask = mask.ravel()
            x = x[mask]
            y = y[mask]
            z = z[mask]

        # Construir matriz de diseño
        A = self._design_matrix(x, y)

        # Ajuste por mínimos cuadrados
        coeffs, _, _, _ = np.linalg.lstsq(A, z, rcond=None)

        # Evaluar el polinomio en toda la imagen
        A_full = self._design_matrix(
            np.mgrid[:h, :w][1].ravel(),
            np.mgrid[:h, :w][0].ravel()
        )

        fondo = (A_full @ coeffs).reshape(h, w)
        return fondo

    def _design_matrix(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Construye la matriz de diseño para el ajuste polinómico.
        """
        terms = []
        for i in range(self.grado + 1):
            for j in range(self.grado + 1 - i):
                terms.append((x ** i) * (y ** j))
        return np.vstack(terms).T