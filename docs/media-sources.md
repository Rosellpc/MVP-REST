# Recursos multimedia — solo enlaces externos

Las fotografías se consumen mediante URLs en `frontend/src/lib/media.ts`.
No se incluyen copias de archivos en el repositorio, según la instrucción del fundador.
Fecha de revisión de las páginas de origen: 25 de septiembre de 2026.

| Recurso | Autor | Fuente | Licencia |
|---|---|---|---|
| Lomo saltado | WikiHes | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Lomo-saltado-perudelights.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Ají de gallina | Feralbt | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Aj%C3%AD_de_gallina.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| Causa | CEllen | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Causa_Peruvian_dish.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Chicha morada | young shanahan | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Chicha_Morada_2017.jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) |

Presentación: encuadre mediante `object-fit: cover` y reducción de tamaño en pantalla.
Las fotos y su encuadre conservan las licencias indicadas; no se atribuye su autoría
a RestaurantOS ni se sugiere el respaldo de sus autores. Mantener las atribuciones
en /credits y la indicación de fotografía referencial.

Estas imágenes no acreditan ingredientes, alérgenos, porciones o disponibilidad reales.
Los originales pueden ser grandes y su proveedor puede limitar solicitudes (HTTP 429).
La interfaz mantiene una reserva de espacio y muestra “Fotografía no disponible”
ante fallos de carga; las acciones de producto siguen funcionando.

Para reemplazar una imagen: verificar licencia y autor → cambiar su URL/fuente/créditos
en media.ts → actualizar esta tabla → comprobar encuadre, texto alternativo y fallback.
No usar descargas, imágenes generadas ni hotlinks con credenciales o URLs temporales.
