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