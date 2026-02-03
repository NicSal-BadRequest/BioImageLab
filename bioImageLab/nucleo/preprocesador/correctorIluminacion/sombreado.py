'''
    Correccion sin flat, basada en la propia imagen
    I(x,y)=S(x,y)⋅L(x,y)
    L = Iluminacion suave estimada

    Metodos : Low pass + division, retinex, ajuste polinomial, estimacion por mediana tempora/z
    corrige : Gradientes suaves, iluminacion desigual cuando no hay flat
'''