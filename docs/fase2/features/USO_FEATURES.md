# Posible uso de la tabla de features

La tabla de features podría utilizarse como entrada para modelos de ciencia
de datos orientados a comprender y anticipar el comportamiento de los
usuarios de la Red Metropolitana.

Un posible caso de uso sería predecir la probabilidad de que un usuario
continúe utilizando activamente la red durante un período futuro.

Variables como la cantidad de eventos recientes, los días desde la última
actividad, el modo más utilizado, la cantidad de modos, la proporción de
viajes en hora pico y el gasto permiten representar diferentes patrones de
uso.

También podría utilizarse para identificar usuarios con mayor probabilidad
de utilizar varios sistemas de transporte o para segmentar perfiles de
movilidad según frecuencia, zona, horario y modo predominante.

Para la Agencia Metropolitana, estos análisis podrían apoyar la planificación
de capacidad, la integración entre operadores y el diseño de estrategias
para grupos de usuarios con diferentes patrones de movilidad.

En esta fase no se entrena un modelo predictivo. El objetivo es dejar una
tabla model-ready, reproducible y con una fecha de corte explícita para que
pueda utilizarse posteriormente sin volver a procesar los datos operacionales.