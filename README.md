# MOTIVO DEL PROYECTO

El pasado 12 de mayo de 2019, el artículo 34.9 del *Estatuto de los Trabajadores* sufrió una reforma, tras la cual todos los trabajadores en España pasaron a tener la obligación de registrar su jornada laboral.

Desde ese momento, muchas empresas comenzaron a implantar en sus respectivos ERP módulos para el registro de jornadas o instalar software específico para este fin. Sin embargo, muchas otras empresas (sobre todo PYMES y autónomos), ante la imposibilidad de asumir el sobrecoste o por desconocimiento de estas tecnologías, optaron por llevar un registro más manual apoyándose en otros medios (formato físico, ficheros Excel, etc.).

En este segundo grupo se encuentra un familiar. Debido al desconocimiento de herramientas que faciliten el fichaje de sus trabajadores y al sobrecoste que supondría su implantación, el registro de las jornadas laborales se realiza de forma manual. Esto implica retrabajo por parte de la responsable del control horario, así como posibles errores humanos y malentendidos entre el personal.

Por ello, con el objetivo de ayudar inicialmente a dicho familiar (y potencialmente a otras empresas en situación similar), he decidido que mi proyecto final del módulo de **Desarrollo de Aplicaciones Multimedia** consista en crear una herramienta sencilla para el usuario final, pero capaz de cubrir todas sus necesidades.

Actualmente, los trabajadores deben llevar un registro personal para comprobar que los fichajes se realizan correctamente por parte de la empresa. En muchas ocasiones, la información del fichaje es proporcionada por el propio trabajador.

Por lo tanto, en este proyecto se desarrollará un módulo en **Odoo** que gestionará el registro y tratamiento de los fichajes. El trabajador informará de su jornada mediante el uso de lectores y tarjetas NFC. De este modo:

- La empresa dispondrá de un registro más controlado y ajustado a la realidad.
- Se habilitarán distintas opciones de gestión de fichajes.
- El trabajador podrá fichar con un simple movimiento, facilitando el proceso.

---

# MVP (PRODUCTO MÍNIMO VIABLE)

A continuación, se detalla lo mínimo necesario para que el proyecto pueda ponerse en funcionamiento:

- Identificación de un trabajador mediante una tarjeta NFC propia.
- Lectura de dicha tarjeta.
- Registro de la información correspondiente al trabajador y la hora exacta.
- Identificación del tipo de fichaje (entrada/salida) y del tipo de hora (normal o extraordinaria).
- Almacenamiento de los fichajes para su posterior tratamiento.
- Permisos para que la responsable de la empresa pueda acceder a los registros.
- Envío de informes tanto al trabajador como al responsable.

---

# REQUISITOS

Los requisitos del sistema se dividen en dos categorías: funcionales y no funcionales.

## Requisitos funcionales

- Tras la lectura de la tarjeta NFC asociada a un trabajador, el módulo debe registrar un nuevo fichaje.
- Según los registros almacenados, el sistema debe identificar si se trata de una entrada o una salida.
- El programa debe ser capaz de identificar horas extraordinarias, horas realizadas en festivo, etc.
- Al final de la jornada o de la semana, el sistema debe enviar un informe al trabajador para su revisión.
- El módulo debe mostrar al responsable los fichajes de cada trabajador para su control.

## Requisitos no funcionales

- El sistema deberá implementarse como un nuevo módulo en el ERP Odoo.
- Se trabajará con la versión 17 de Odoo.
- Los datos se almacenarán y gestionarán en la base de datos proporcionada por Odoo.
- El lector NFC deberá conectarse correctamente con Odoo.
- El módulo gestionará permisos según distintos roles de usuario.

---

# CASOS DE USO

A continuación, se detallan algunos casos de uso del sistema.


| Caso de uso: Registro fichaje empleado |
|-----------------------------------------|
| ID: CU-1 |
| **Descripción:** el empleado aproxima su tarjeta personal por el lector NFC instalado por la empresa. A través de este, el sistema recoge el número identificativo del empleado registrado en su tarjeta NFC, realiza las comprobaciones necesarias y registra el fichaje en la BBDD con la información necesaria. |
| **Actores:** empleado, tarjeta personal y lector NFC. |
| **Precondiciones:** se requiere que el empleado esté registrado en el sistema, su número identificativo personal esté registrado en su tarjeta personal y el lector NFC esté configurado correctamente. |
| **Curso normal del caso de uso:**<br>1- El empleado acerca su tarjeta personal al lector NFC.<br>2- El lector NFC lee el número identificativo del trabajador.<br>3- El sistema busca dicho número en la BBDD.<br>4- El sistema revisa el último fichaje del empleado para determinar el tipo de fichaje (entrada/salida).<br>5- El sistema registra el fichaje.<br>6- El sistema confirma el fichaje mediante un mensaje. |
| **Postcondiciones:** el fichaje queda registrado correctamente en la BBDD. |
| **Alternativa 1:**<br>2.1- La tarjeta no tiene asociado ningún número identificativo.<br>2.2- El sistema informará al empleado que no ha conseguido leer la tarjeta.<br>2.3- Fin del caso de uso. |
| **Alternativa 2:**<br>3.1- El sistema no localiza el número asociado a la tarjeta pasada.<br>3.2- El sistema informará al empleado que no se ha encontrado dicho número.<br>3.3- Fin del caso de uso. |

<br>

| Caso de uso: Consulta de fichajes por parte de la responsable |
|-------------------------------------------------------------|
| ID: CU-2 |
| **Descripción:** la responsable indica el empleado y los días que quiere consultar los fichajes y el sistema devuelve un informe con todos los fichajes realizados dichos días y una serie de indicadores como las horas teóricas trabajadas, las horas reales y las horas extraordinarias. |
| **Actores:** responsable. |
| **Precondiciones:** la responsable debe tener permisos de consulta. |
| **Curso normal del caso de uso:**<br>1- La responsable accede al módulo con sus credenciales.<br>2- La responsable indica el trabajador sobre el que quiere consultar los fichajes.<br>3- La responsable indica el rango de días sobre los que quiere hacer la consulta.<br>4- El sistema busca los fichajes realizados según los parámetros indicados en los puntos 2 y 3.<br>5- El sistema prepara el informe realizando los cálculos necesarios por cada día consultado.<br>6- El sistema muestra el informe con los datos por pantalla.<br>7- El sistema da opción de generar un documento .xlsx. |
| **Postcondiciones:** la responsable obtiene el informe solicitado para su control y tratamiento. |
| **Alternativa 1:**<br>4.1- El sistema no encuentra fichajes.<br>4.2- El sistema informa por pantalla al responsable.<br>4.3- Fin del caso de uso. |

<br>

| Caso de uso: Envío informe semanal al empleado |
|------------------------------------------------|
| ID: CU-3 |
| **Descripción:** semanalmente, se ejecuta un job para que el sistema le remita un informe a cada empleado con las horas efectuadas dicha semana para su revisión. |
| **Actores:** sistema y empleado. |
| **Precondiciones:** deben existir fichajes en la semana a enviar el informe y el sistema debe tener registrado el correo electrónico del empleado. |
| **Curso normal del caso de uso:**<br>1- El sistema ejecuta job semanal.<br>2- El sistema consulta datos empleado por empleado.<br>3- El sistema determina el rango de fechas sobre los que generar el informe.<br>4- El sistema genera informes según los parámetros determinados en los puntos 2 y 3.<br>5- El sistema envía los informes por correo electrónico. |
| **Postcondiciones:** cada empleado recibe el informe de su jornada laboral de la semana tratada. |
| **Alternativa 1:**<br>2.1- El sistema no localiza registro de correo electrónico para un empleado.<br>2.2- El sistema informa por correo electrónico al responsable para subsanar esta situación.<br>2.3- Fin del caso de uso. |
| **Alternativa 2:**<br>4.1- El sistema no encuentra fichajes de un empleado en el rango de fechas indicado.<br>4.2- El sistema notifica la ausencia de registros al empleado por correo electrónico.<br>4.3- Fin del caso de uso. |

<br>

| Caso de uso: Registro manual de un fichaje de empleado |
|--------------------------------------------------------|
| ID: CU-4 |
| **Descripción:** la responsable podrá registrar un fichaje manualmente con la información facilitada por el empleado y validada por ella. |
| **Actores:** responsable y empleado |
| **Precondiciones:** la responsable tiene permisos para el registro manual de fichajes de empleados y el empleado esté registrado en el sistema. |
| **Curso normal del caso de uso:**<br>1- La responsable accede al módulo con sus credenciales.<br>2- La responsable indica el empleado sobre el que quiere registrar el fichaje.<br>3- La responsable indica el día del fichaje.<br>4- La responsable indica la hora del fichaje.<br>5- El sistema determina el tipo de fichaje según la fecha y la hora indicada.<br>6- El sistema registra el fichaje.<br>7- El sistema confirma el fichaje mediante un mensaje. |
| **Postcondiciones:** el fichaje queda registrado correctamente en la BBDD. |
| **Alternativa 1:** ninguna. |

---

# DIAGRAMA ENTIDAD-RELACIÓN (E-R)

## Entidades

#### EMPLEADO
Registro de los empleados de la empresa. Se valora utilizar la propia tabla de empleados de Odoo, quedando esta sin crear.

| Atributo      | Tipo          | Descripción |
|---------------|---------------|-------------|
| `ID_EMPLEADO` | INTEGER (PK)  | Identificador único del empleado |
| `NOMBRE`      | VARCHAR(50)   | Nombre del empleado |
| `APELLIDO1`   | VARCHAR(50)   | Primer apellido |
| `APELLIDO2`   | VARCHAR(50)   | Segundo apellido |
| `TELEFONO`    | INTEGER       | Teléfono de contacto |
| `EMAIL`       | VARCHAR(50)   | Correo electrónico |


#### FICHAJE
Registro de los fichajes realizados por los empleados.

| Atributo        | Tipo              | Descripción |
|-----------------|-------------------|-------------|
| `ID_FICHAJE`    | INTEGER (PK)      | Identificador de fichaje (único por empleado) |
| `ID_EMPLEADO`   | INTEGER (PK, FK)  | Identificador del empleado que realiza el fichaje |
| `FECHA_FICHAJE` | DATE              | Fecha del fichaje |
| `HORA_FICHAJE`  | TIME              | Hora del fichaje |
| `TIPO_FICHAJE`  | VARCHAR(25)       | Tipo de fichaje (entrada/salida) |

**Clave primaria compuesta:**  
`(ID_FICHAJE, ID_EMPLEADO)`

**Clave foránea:**  
`ID_EMPLEADO → EMPLEADO(ID_EMPLEADO)`


## Relaciones

### Empleado — Fichaje
- **Relación 1:N**   
  Un empleado puede tener múltiples fichajes.  
  Cada fichaje pertenece a un único empleado.

EMPLEADO (1) ───────────< (N) FICHAJE

## Diagrama E-R

![Diagrama E-R](https://github.com/Seradjor/PFC/blob/main/Images/E-R.png)

---

## DIAGRAMA DE DESPLIEGUE

![Diagrama de despliegue](https://github.com/Seradjor/PFC/blob/main/Images/Diagrama%20de%20despliegue.png)

---

## WIREFRAMES (VISUALIZACIÓN DE LA APLICACIÓN)

## Lector NFC

### Fichaje realizado
![Fichaje realizado](https://github.com/Seradjor/PFC/blob/main/Images/Fichaje%20realizado.png)

### Número de tarjeta no encontrado
![Número de tarjeta no encontrado](https://github.com/Seradjor/PFC/blob/main/Images/N%C3%BAmero%20tarjeta%20no%20encontrado.png)

### Error lectura tarjeta
![Error lectura tarjeta](https://github.com/Seradjor/PFC/blob/main/Images/Error%20lectura%20tarjeta.png)

## Módulo Odoo

### Selección fichajes
![Selección fichajes](https://github.com/Seradjor/PFC/blob/main/Images/Selecci%C3%B3n%20fichajes.png)

### Fichajes no encontrados
![Fichajes no encontrados](https://github.com/Seradjor/PFC/blob/main/Images/Fichajes%20no%20encontrados.png?raw=true)

### Visualización fichajes
![Visualización fichajes](https://github.com/Seradjor/PFC/blob/main/Images/Visualizaci%C3%B3n%20fichajes.png)

### Registro fichaje manual
![Registro fichaje manual](https://github.com/Seradjor/PFC/blob/main/Images/Registro%20fichaje%20manual.png)

### Edición fichajes
![Edición fichajes](https://github.com/Seradjor/PFC/blob/main/Images/Edici%C3%B3n%20fichajes.png)

## Medio de contacto (correo)

### Informe fichaje semanal
![Informe fichaje semanal](https://github.com/Seradjor/PFC/blob/main/Images/Wireframe%20correo%20fichaje%20semanal.png)

### Aviso falta de datos empleado para envío informe semanal
![Aviso falta de datos empleado para envío informe semanal](https://github.com/Seradjor/PFC/blob/main/Images/Aviso%20falta%20de%20datos%20empleado%20para%20env%C3%ADo%20informe%20semanal.png)

### Aviso no registro de fichajes en informe semanal
![Aviso no registro de fichajes en informe semanal](https://github.com/Seradjor/PFC/blob/main/Images/Aviso%20no%20registro%20de%20fichajes%20en%20informe%20semanal.png)
