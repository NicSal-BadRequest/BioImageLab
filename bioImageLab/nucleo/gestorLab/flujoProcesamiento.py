class FlujoProcesamiento:
    """
        Clase que gestiona un flujo de operaciones atomicas de filtrado, suavizado, segmentacion y deteccion
        en bioimagenes.
        Permite: 
        - Almacenar temporalmente las imagenes procesadas en un diccionario cuya clave 
        fue la operacion aplicada y su valor el MultiArray imagen.
        - Almacenar y utilizar una lista de diccionarios los cuales tienen por clave y valores los nombres de las
        operaciones y parametros aplicados (mapped) a los valores de dichos parametros. Es decir, como
        ejemplo:
            {
                nombre_operacion : "gaussiano",
                mascara : (3,3),
                sigma : 75
            }
    """

    def __init__(self, img: np.ndarray):
        self.img_original = img
        self.procesados : Dict[str, np.ndarray] = {}
        self.operaciones : List[dict] = []

    def ejecutar(self, nombre: str, operacion):
        resultado = operacion(self.img_original)
        self.procesados[nombre] = resultado

        self.operaciones.append({
            "operacion" : operacion.__clas__.__name__,
            "parametros" : operacion.__dict__
        })

        return resultado