# Spec 001 — Configuración de negocio de comida

## 1. Contexto y objetivo

**Contexto.** ChatBotAI atiende por WhatsApp a negocios que hoy tienen plantillas de propósito mezclado: existe una plantilla de citas heredada de un enfoque de estética y una de producto que ya no se usa. El sistema decide de antemano qué hace un negocio según un tipo de servicio, de modo que crecer obliga a modificarlo cada vez.

Se decide **reducir el enfoque a un solo nicho**: negocios de comida, con entrega **a domicilio, consumo en local o pickup**. A cambio, todo lo que varía entre un negocio y otro —su menú, sus locales, sus horarios, sus formas de entrega y las plantillas que el asistente usa— pasa a ser **configuración del propio negocio**, no una decisión fija del sistema.

**Objetivo.** Que un negocio de comida pueda configurarse por completo —su catálogo, sus locales y las plantillas que el asistente usará— **sin que nadie tenga que modificar el sistema** para darlo de alta.

---

## 2. Usuarios

| Perfil | Qué hace |
|---|---|
| **Administrador del sistema** | Define los nichos y crea las plantillas que usarán los negocios. Único perfil que puede crear plantillas personalizadas. |
| **Dueño del negocio** | Configura el menú base, las categorías, las relaciones de ingredientes, las formas de entrega, el mínimo de pedido y sus locales. **No edita plantillas.** |
| **Administrador de local** | Gestiona solo su local: añade platos exclusivos, descarta los que no ofrece, y ajusta versiones de artículos sin tocar a los demás locales. |
| **Operador multi-negocio** | Gestiona varios negocios desde un mismo panel. Requiere permiso de edición, definido en una spec aparte. |

---

## 3. Historias de usuario

- **HU-1** — Como dueño de un negocio de comida, quiero configurar el menú **una sola vez** y elegir en qué locales se aplica, para no repetir trabajo en cada sucursal.
- **HU-2** — Como dueño, quiero que cada local tenga su dirección, sus horarios y su propio número de WhatsApp, para que cada sucursal atienda por su lado.
- **HU-3** — Como dueño, quiero declarar qué formas de entrega acepto y si hay pedido mínimo, para no aceptar pedidos que no puedo servir.
- **HU-4** — Como dueño, quiero indicar qué ingredientes se pueden quitar de un plato y qué extras admite, para que el cliente personalice sin pedir imposibles.
- **HU-5** — Como dueño, quiero ocultar un artículo sin borrarlo, para sacarlo del menú hoy y volver a ponerlo mañana.
- **HU-6** — Como administrador de local, quiero añadir platos exclusivos de mi local y marcar otros como no disponibles aquí, para adaptar el menú a mi sucursal.
- **HU-7** — Como administrador de local, quiero que un ajuste mío no afecte a los demás locales, para no romperle la configuración a nadie.
- **HU-8** — Como operador multi-negocio, quiero gestionar varios negocios desde un mismo panel, para no entrar y salir de cuentas.
- **HU-9** — Como administrador del sistema, quiero que cada negocio nuevo arranque con las plantillas de su nicho ya puestas, para que nadie tenga que definirlas a mano.
- **HU-10** — Como dueño, quiero ver qué me falta para tener el negocio listo, para saber cuándo ya puedo recibir pedidos.

---

## 4. Requisitos funcionales

### 4.1 Negocio y locales

**RF-1.** El sistema debe permitir crear un negocio con su identificación y su nicho.
- *CA1: Donde no existe ningún negocio con ese nombre, cuando el dueño lo crea, el sistema debe guardarlo y ofrecerle configurarlo.*
- *CA2: Donde ya existe un negocio con ese nombre, cuando el dueño intenta crearlo, el sistema debe rechazarlo avisando del conflicto.*

**RF-2.** El sistema debe permitir que un negocio tenga **varios locales**, cada uno con su dirección y **su propio número de WhatsApp**.
- *CA1: Cuando el dueño añade un local, el sistema debe registrarlo distinguido del resto dentro del mismo negocio.*
- *CA2: Donde un negocio tiene varios locales, el sistema debe mantener separadas las conversaciones de cada local.*

**RF-3.** El sistema debe permitir que cada local declare sus **horarios de atención** por día de la semana y marque días como cerrado.
- *CA1: Donde un local tiene un día marcado como cerrado, el sistema debe reflejar ese estado al consultar sus horarios.*
- *CA2: Cuando un local guarda sus horarios, el sistema debe conservarlos sin afectar a los horarios de los demás locales.*

### 4.2 Entregas y mínimo de pedido

**RF-4.** El sistema debe permitir definir las **formas de entrega** que se aceptan (a domicilio, consumo en local, pickup), con una base del negocio que cada local puede ajustar.
- *CA1: Cuando el dueño define las formas de entrega del negocio, el sistema debe ofrecerlas por defecto a todos sus locales.*
- *CA2: Cuando un local ajusta sus propias formas de entrega, el sistema debe conservar ese ajuste solo para ese local.*
- *CA3: Donde un local no ha hecho ningún ajuste, el sistema debe aplicarle la base del negocio.*

**RF-5.** El sistema debe permitir definir el **pedido mínimo**, con una base del negocio que cada local puede ajustar.
- *CA1: Cuando el dueño fija el mínimo del negocio, el sistema debe ofrecerlo por defecto a todos sus locales.*
- *CA2: Cuando un local fija su propio mínimo, el sistema debe prevalecer sobre la base, solo para ese local.*

### 4.3 Menú base

**RF-6.** El sistema debe permitir registrar artículos del menú con **nombre, precio, descripción, imagen y categoría**.
- *CA1: Cuando el dueño guarda un artículo con todos sus datos, el sistema debe incorporarlo al menú base del negocio.*
- *CA2: Donde un artículo carece de precio, cuando el dueño intenta guardarlo, el sistema debe rechazarlo avisando de qué campo falta.*

**RF-7.** El precio de un artículo es obligatorio, debe ser un número **mayor o igual que cero**, y el cero significa artículo gratuito.
- *CA1: Donde el precio es cero, el sistema debe guardar el artículo como gratuito.*
- *CA2: Donde el precio es negativo o no es un número, cuando el dueño intenta guardarlo, el sistema debe rechazarlo.*

**RF-8.** El sistema debe impedir que dos artículos de un mismo negocio compartan nombre, avisando al guardar.
- *CA1: Donde ya existe un artículo con ese nombre en el negocio, cuando el dueño intenta guardar otro igual, el sistema debe rechazarlo indicando el nombre duplicado.*
- *CA2: Donde el nombre es único en el negocio, el sistema debe aceptarlo aunque coincida con el de otro negocio.*
- *CA3: Donde un local guarda su propia versión de un artículo existente, el sistema debe tratarla como versión y no como duplicado.*

**RF-9.** El sistema debe permitir al dueño crear y renombrar las **categorías** del menú; las categorías pertenecen al negocio y se comparten entre sus locales.
- *CA1: Cuando el dueño crea una categoría, el sistema debe ofrecerla para clasificar artículos en todos los locales del negocio.*
- *CA2: Donde una categoría no tiene artículos, el sistema debe permitir eliminarla sin afectar al resto del menú.*
- *CA3: Donde un local añade un artículo propio, el sistema debe exigirle elegir una categoría del negocio.*

**RF-10.** El sistema debe permitir marcar un artículo como **inactivo**, de modo que desaparezca del menú sin perder su registro.
- *CA1: Cuando un artículo se marca inactivo, el sistema debe dejar de ofrecerlo en el menú.*
- *CA2: Cuando se vuelve a activar, el sistema debe recuperarlo con todos sus datos y relaciones intactas.*

**RF-11.** El sistema debe permitir al dueño del negocio **elegir en qué locales** se aplica un artículo del menú base.
- *CA1: Cuando el dueño añade un artículo, el sistema debe pedirle que seleccione los locales que lo recibirán.*
- *CA2: Donde el dueño no selecciona ningún local, el sistema debe conservar el artículo solo en el menú base.*

**RF-12.** El sistema debe permitir al dueño del negocio **retirar un artículo de los locales que elija**, seleccionando en una lista **qué locales lo conservan**. El artículo **se queda en el menú base**.
- *CA1: Cuando el dueño retira un artículo, el sistema debe mostrarle la lista de sus locales para que elija cuáles lo conservan.*
- *CA2: Donde un local no fue seleccionado, el sistema debe retirarle ese artículo.*
- *CA3: Donde un local fue seleccionado, el sistema debe conservarle el artículo sin importar que tenga versión propia.*
- *CA4: Donde todos los locales fueron deseleccionados, el sistema debe conservar el artículo en el menú base para poder volver a aplicarlo.*

### 4.4 Ingredientes, extras y relaciones

**RF-13.** El sistema debe permitir declarar, artículo por artículo, **qué ingredientes propios se pueden quitar**.
- *CA1: Donde un plato declara ingredientes quitables, el sistema debe distinguirlos de los que forman parte fija del plato.*
- *CA2: Cuando el dueño deja de declarar un ingrediente como quitable, el sistema debe dejar de ofrecerlo como tal, sin borrar el artículo.*

**RF-14.** El sistema debe permitir declarar **qué extras admite cada artículo**, en **un solo nivel**: los extras no admiten los suyos.
- *CA1: Donde un artículo tiene extras declarados, el sistema debe asociarlos solo a ese artículo.*
- *CA2: Donde un artículo está declarado como extra, el sistema no debe permitir que a su vez tenga extras.*

**RF-15.** Los ingredientes y extras deben ser **artículos reutilizables**: al declararlos para un plato, el sistema debe buscar si ya existe y, si no, crearlo, para poder usarlo en otros platos.
- *CA1: Donde el ingrediente ya existe en el negocio, cuando se declara en otro plato, el sistema debe vincular el artículo existente sin duplicarlo.*
- *CA2: Donde no existe, cuando se declara, el sistema debe crearlo como artículo y vincularlo.*

**RF-16.** El sistema debe permitir **borrar un artículo** y, al hacerlo, limpiar las relaciones que apuntaban a él avisando de cuántas afecta.
- *CA1: Cuando se borra un artículo que otros usan como extra o ingrediente quitable, el sistema debe eliminar esas relaciones y avisar de cuántas.*
- *CA2: Donde ningún artículo lo referenciaba, el sistema debe borrarlo sin aviso de relaciones.*

### 4.5 Menú de cada local

**RF-17.** Cada local debe tener **su propio menú**, construido a partir del menú base del negocio.
- *CA1: Cuando un local recibe un artículo del menú base, el sistema debe incorporarlo a su menú.*
- *CA2: Donde un local no ha recibido un artículo, el sistema no debe ofrecérselo.*

**RF-18.** El administrador de local debe poder **añadir platos exclusivos de su local**.
- *CA1: Cuando el administrador de local añade un plato, el sistema debe registrarlo solo en ese local.*
- *CA2: Donde el plato ya existe en el menú base, el sistema debe tratarlo como versión propia y no como artículo nuevo.*

**RF-19.** El administrador de local debe poder marcar un artículo como **"no disponible en este local"**, de forma **reversible**.
- *CA1: Cuando el administrador de local descarta un artículo, el sistema debe dejar de ofrecerlo solo en ese local.*
- *CA2: Cuando el administrador de local lo reactiva, el sistema debe devolverlo con todos sus datos y relaciones intactos.*
- *CA3: Donde el artículo está descartado, el sistema no debe dejar rastro de él en el menú de ese local.*

**RF-20.** El administrador de local debe poder editar un artículo del menú base **sin que el cambio afecte a los demás locales**.
- *CA1: Cuando un local modifica un artículo, el sistema debe conservar la modificación solo para ese local.*
- *CA2: Donde dos locales modifican el mismo artículo de forma distinta, el sistema debe mantener cada versión por separado.*

**RF-21.** Los cambios que el dueño hace sobre el menú base deben **propagarse a todos los locales, salvo a los que ya tengan versión propia o lo hayan descartado**.
- *CA1: Donde un local no ha tocado el artículo, cuando el negocio lo cambia, el sistema debe aplicarle el cambio.*
- *CA2: Donde un local ya lo modificó, cuando el negocio lo cambia, el sistema debe conservar la versión de ese local y no pisarla.*
- *CA3: Donde un local lo tiene descartado, el sistema no debe reponerlo por el cambio del negocio.*

### 4.6 Plantillas

**RF-22.** Cada negocio debe contar con una **plantilla de datos**: el estado que el asistente mantiene y completa mientras atiende a un cliente. Para el nicho de comida debe cubrir:
- tipo de compra (domicilio, consumo en local, pickup),
- local elegido,
- lista de artículos con sus extras y sus ingredientes quitados,
- dirección de entrega (solo si es a domicilio),
- datos de contacto,
- total,
- estado de confirmación.

*CA1: Donde un negocio no tiene ningún estado en curso, el sistema debe ofrecer la plantilla de datos de su nicho.*
*CA2: Donde ya hay un estado en curso, el sistema debe ofrecer ese estado y no la plantilla base.*
*CA3: Donde la forma de compra es a domicilio, el sistema debe considerar obligatoria la dirección.*
*CA4: Donde la forma de compra no es a domicilio, el sistema no debe exigir dirección.*

**RF-23.** Cada negocio debe contar con una **plantilla de respuesta**, que debe devolver como mínimo: **el mensaje para el cliente**, **la plantilla de datos actualizada**, **la acción que guía la conversación** y **el objeto que se mapea al menú interactivo**.
- *CA1: Cuando el negocio es creado, el sistema debe asignarle la plantilla de respuesta de su nicho.*
- *CA2: Donde la respuesta carece de alguno de los cuatro elementos, el sistema debe rechazarla como inválida.*

**RF-24.** Las plantillas deben crearse **por prioridad de llenado**: cada dato tiene un orden definido en la plantilla.
- *CA1: Cuando el asistente necesita un dato, debe tomarlo del punto de mayor prioridad que aún esté vacío.*
- *CA2: Donde un dato ya está rellenado, el sistema debe saltarlo y pasar al siguiente.*

**RF-25.** Antes de dar un pedido por confirmado, el sistema debe **pedir siempre la confirmación explícita del cliente**, aunque todos los datos estén rellenados.
- *CA1: Donde todos los datos están completos, el sistema debe presentar el resumen y esperar la confirmación antes de darlo por cerrado.*
- *CA2: Donde el cliente aún no confirma, el sistema no debe considerar confirmado el pedido.*

**RF-26.** Las plantillas deben soportar **dos modalidades de entrada**: el menú interactivo de WhatsApp con respuestas paso a paso, y el **texto libre que el backend valida antes de escribirlo**.
- *CA1: Cuando el cliente elige una opción del menú interactivo, el sistema debe tomarla como respuesta válida.*
- *CA2: Cuando el cliente escribe su propia respuesta, el sistema debe validarla contra la plantilla y contra los datos del negocio o del local antes de escribirla.*
- *CA3: Donde la respuesta escrita sobrescribe un dato ya rellenado, el sistema debe pedir confirmación antes de reemplazarlo.*
- *CA4: Donde la respuesta no es coherente con la plantilla ni con los datos del negocio, el sistema debe rechazarla y volver a preguntar.*
- *CA5: Cuando el cliente pide cancelar o cambiar algo de su pedido, el sistema debe atenderlo sin reescribir nada hasta recibir confirmación explícita.*

**RF-27.** El sistema debe ofrecer un **conjunto de acciones** para guiar la conversación: ninguna, mostrar menú, mostrar extras y quitos de un plato, mostrar formas de entrega, mostrar horarios, pedir dirección, pedir local, confirmar pedido, cancelar pedido y **ver pedido**.
- *CA1: Cuando el asistente necesita que el cliente vea algo concreto, debe devolver la acción correspondiente.*
- *CA2: Donde ninguna acción aplica, el sistema debe devolver la acción de "ninguna".*
- *CA3: Cuando el cliente pide ver su pedido, el sistema debe poder responder con la acción de "ver pedido".*

**RF-28.** El objeto que se mapea al menú interactivo debe poder representar, como mínimo: **secciones del menú, menú general o de la sección escogida, extras y quitos de un plato, y horarios**.
- *CA1: Cuando la acción es mostrar el menú, el objeto debe describir las secciones a ofrecer.*
- *CA2: Cuando la acción es mostrar los extras de un plato, el objeto debe describir las opciones de ese plato.*
- *CA3: Donde la acción no requiere opciones que elegir, el sistema no debe generar objeto de menú.*

**RF-29.** El dueño del negocio **no debe poder editar las plantillas**; su contenido lo define el nicho.
- *CA1: Donde el perfil es dueño del negocio o administrador de local, el sistema no debe ofrecerle edición de plantillas.*
- *CA2: Donde el perfil es administrador del sistema, el sistema debe permitirle definir plantillas personalizadas para un nicho.*

### 4.7 Presentación del menú

**RF-30.** El menú debe presentarse **primero por categorías y, dentro de la elegida, en bloques**, de modo que nunca se ofrezca una lista tan extensa que sature al cliente.
- *CA1: Cuando se pide ver el menú, el sistema debe ofrecer primero las categorías.*
- *CA2: Cuando el cliente elige una categoría, el sistema debe ofrecer sus artículos en bloques.*
- *CA3: Donde una categoría no cabe entera en un bloque, el sistema debe ofrecer la continuación del resto.*

### 4.8 Estado de la configuración

**RF-31.** El sistema debe permitir **guardar la configuración aunque esté incompleta**, marcándolo e indicando qué falta.
- *CA1: Cuando el dueño guarda una configuración sin artículos o sin formas de entrega, el sistema debe conservarla y marcarla como incompleta.*
- *CA2: Donde la configuración reúne todo lo necesario, el sistema debe dejar de marcarla como incompleta.*
- *CA3: Donde un negocio está incompleto, el sistema debe informar de qué le falta hasta completarlo.*

---

## 5. Requisitos no funcionales

- **RNF-1.** La configuración de un negocio **no debe poder leerse ni alterarse desde otro negocio**: cada uno debe operar sobre lo suyo.
- **RNF-2.** El sistema debe entregar al asistente **el menú completo de un solo acceso**, sin importar cuántos artículos, categorías o locales tenga.
- **RNF-3.** Un negocio con varios locales no debe duplicar el trabajo de configuración: el menú se define una vez y se reparte.
- **RNF-4.** Los cambios de configuración deben reflejarse en la siguiente atención, sin pasos intermedios ni recargas manuales.
- **RNF-5.** El menú ofrecido al cliente **nunca debe exceder el límite de opciones** que admite el menú interactivo: siempre debe haber una vía para llegar al resto.
- **RNF-6.** Los perfiles solo deben ver y poder hacer las acciones propias de su rol.

---

## 6. Casos límite

| # | Caso límite | Comportamiento esperado |
|---|---|---|
| CL-1 | Negocio recién creado, sin nada configurado | Se guarda; queda **incompleto** con aviso de qué falta (RF-31) |
| CL-2 | Artículo sin precio | Rechazado al guardar (RF-6) |
| CL-3 | Precio `0` | Válido: artículo gratuito (RF-7) |
| CL-4 | Precio negativo o no numérico | Rechazado al guardar (RF-7) |
| CL-5 | Dos artículos con el mismo nombre en el negocio | Rechazado con aviso (RF-8) |
| CL-6 | Un local guarda su versión de un artículo existente | Se acepta como **versión propia**, no como duplicado (RF-8) |
| CL-7 | Borrar artículo usado como extra en otros platos | Se borra y se limpian las relaciones avisando (RF-16) |
| CL-8 | Intentar que un extra tenga sus propios extras | Impedido: un solo nivel (RF-14) |
| CL-9 | Declarar un ingrediente que ya existe | Se reutiliza, no se duplica (RF-15) |
| CL-10 | Retira un plato de todos sus locales | Se retira de todos, pero **se queda en el menú base** para poder volver a aplicarlo (RF-12) |
| CL-11 | Retira un plato y marca dos locales para conservarlo | Solo esos dos lo conservan; el resto lo pierde (RF-12) |
| CL-12 | Local con plato descartado y el negocio actualiza ese plato | Se conserva descartado; el cambio no lo repone (RF-21) |
| CL-13 | Local que edita un artículo modificado después por el negocio | Se conserva la versión del local; no se pisa (RF-21) |
| CL-14 | Dos locales con versiones distintas del mismo artículo | Ambas conviven, separadas por local (RF-20) |
| CL-15 | Local que reactiva un plato descartado | Vuelve con sus datos y relaciones intactos (RF-19) |
| CL-16 | Local sin horarios declarados | Configuración **incompleta** (RF-31) |
| CL-17 | Categoría vacía al intentar eliminarla | Permitido sin afectar al resto (RF-9) |
| CL-18 | Dueño del negocio intenta editar una plantilla | No se le ofrece la acción (RF-29) |
| CL-19 | Local añade un plato propio sin elegir categoría | Rechazado: debe usar una categoría del negocio (RF-9) |
| CL-20 | El cliente escribe un dato ya rellenado | Se pide confirmación antes de sobrescribirlo (RF-26) |
| CL-21 | El cliente escribe algo incompatible con la plantilla | Se rechaza y se vuelve a preguntar (RF-26) |
| CL-22 | El cliente pide cambiar o cancelar su pedido | Se atiende sin reescribir nada hasta confirmación explícita (RF-26) |
| CL-23 | Pedido con todos los datos completos | Se presenta resumen y se espera confirmación (RF-25) |
| CL-24 | Categoría con más artículos de los que caben en un bloque | Se ofrecen por bloques con continuación (RF-30) |
| CL-25 | Forma de compra sin dirección cuando es a domicilio | La dirección es obligatoria (RF-22) |
| CL-26 | Forma de compra que no es a domicilio | No se exige dirección (RF-22) |
| CL-27 | Cambio de configuración mientras hay atención en curso | La siguiente atención recibe el nuevo estado (RNF-4) |
| CL-28 | Administrador de local intenta modificar otro local | No se le ofrece esa acción (RNF-6) |

---

## 7. Fuera de alcance

- **La conversación con el cliente**: recibir mensajes, mantener la sesión, avanzar por la plantilla, validar el texto libre y responder. Su definición completa va en la spec de conversación. Quedan ahí, entre otros: que el bot **avise si el local está cerrado** (los horarios se registran aquí, su efecto no), que el bot **evite que el cliente se desvíe del tema**, y el comportamiento detallado del menú interactivo en cada paso.
- **Los permisos y roles del panel** para el operador multi-negocio (se creará aparte).
- **El pedido como tal**: toma de pedido, cobro, historial de órdenes y entrega al negocio.
- **El menú en PDF**: el dueño podrá subir el PDF de su menú y el bot podrá ofrecerlo si existe; queda fuera de esta spec, que solo deja abierta esa posibilidad.
- **El panel/dashboard en sí**: interfaces y pantallas.
- **La definición del asistente**: qué dice, cómo redacta, qué modelo usa.
- **Los datos existentes**: el borrado de lo que hay hoy en la base (negocio, artículos y conversaciones) se hace **de forma manual antes de aplicar esta spec**, sobre una base ya limpia.

---

## 8. Criterios de finalización

1. Todos los **RF-1 a RF-31** tienen sus criterios de aceptación verificados con un caso real.
2. Los **casos límite CL-1 a CL-28** se han provocado y responden como indica la tabla.
3. Un negocio de comida puede quedar **configurado por completo** sin intervención de nadie del sistema.
4. Un negocio con **dos locales** define su menú una vez y cada local conserva sus propias ediciones, sus platos exclusivos, sus descartes, su dirección, sus horarios y su número.
5. El dueño **no puede editar plantillas** y el administrador del sistema sí puede crear plantillas personalizadas.
6. El menú ofrecido al cliente se presenta **por categorías y en bloques** y nunca excede el límite de opciones del menú interactivo.
7. Un pedido de comida puede quedar descrito completo en la plantilla de datos, incluidos extras, quitos, dirección cuando aplica y estado de confirmación.
8. La plantilla de respuesta contiene **los cuatro elementos** (mensaje, plantilla, acción y objeto de menú) y soporta **las dos modalidades** de entrada.
9. Ningún requisito de este spec exige **modificar el sistema** para atender un negocio nuevo.
10. **Ninguna duda abierta** queda marcada como `[NECESITA ACLARACIÓN]`.

---

## 9. Dudas abiertas

No quedan dudas abiertas. Todas las ambigüedades se resolvieron durante la definición del spec y están reflejadas en los requisitos, los casos límite o la sección de fuera de alcance.

### Decisiones que deben revisarse antes de ejecutar

- **Borrado de los datos existentes**: se decidió descartar todo lo que hay hoy (negocio, artículos, conversaciones y mensajes). Es **irreversible**, y queda fuera de esta spec: se hará **de forma manual antes** de aplicarla.
