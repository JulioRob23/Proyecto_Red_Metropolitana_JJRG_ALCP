## Resultado de la auditoría de fuga

Para comprobar que las features no utilizan información posterior a la fecha
de corte, calculamos el corte A de dos formas:

1. utilizando los datos completos disponibles;
2. simulando que únicamente existían datos hasta el 30 de junio de 2026.

En ambos casos se obtuvieron 59,999 unidades.

- Filas con datos completos: 59,999
- Filas con datos recortados: 59,999
- Diferencias encontradas: 0

Por lo tanto, la prueba de recorte fue superada. Las features calculadas para
el corte A son exactamente iguales aunque se elimine toda la información
posterior al 30 de junio, lo que confirma que no utilizan información futura.

También se ejecutaron pruebas de calidad para verificar que existe una sola
fila por unidad y fecha de corte, que las ventanas temporales son consistentes,
que las proporciones se encuentran entre 0 y 1 y que las etiquetas están
disponibles únicamente cuando corresponde.

## Correcciones realizadas

La tabla de features del Proyecto 1 tenía una fecha de corte fija y utilizaba
una ventana de hasta 30 días. Además, varias variables no limitaban
explícitamente la información a eventos anteriores a la fecha de corte.

Para el Proyecto 2 se corrigió la lógica para utilizar exclusivamente:

fecha_corte - 28 días <= fecha_hora < fecha_corte

Se ajustaron las variables de frecuencia, recencia, modos utilizados, gasto,
hora pico, día hábil, modo principal y zona frecuente.

Finalmente, el modelo fue parametrizado mediante `fecha_corte`, permitiendo
utilizar la misma lógica para los cortes A, B y C.