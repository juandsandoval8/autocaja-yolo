# **TECNOLOGIAS EMERGENTES APLICADAS - CAJA REGISTRADORA**

Sistema desarrollado en Python que implementa detección automática de productos mediante visión por computadora, con el objetivo de optimizar procesos comerciales, reducir errores humanos y mejorar la eficiencia operativa.

---

## **Descripción**

Este proyecto consiste en el desarrollo de una caja registradora inteligente basada en técnicas de visión artificial y reconocimiento de imágenes. El sistema es capaz de identificar productos automáticamente a partir de imágenes, eliminando la necesidad de ingreso manual.

Se basa en un modelo de detección de objetos tipo YOLO, entrenado con un dataset previamente recolectado, organizado y etiquetado para reconocer diferentes clases de productos en tiempo real.

---

## **Características**

- Detección automática de productos  
- Procesamiento en tiempo real  
- Modelo basado en YOLO  
- Arquitectura modular usando POO  
- Interfaz gráfica para interacción con el usuario  
- Evaluación del modelo en distintos escenarios  

---

## **Tecnologías utilizadas**

- Python  
- OpenCV  
- YOLO (You Only Look Once)  
- Librerías de procesamiento de imágenes  
- Herramientas de etiquetado de datos  

---

## **Dataset**

El sistema utiliza un [conjunto de datos de imágenes](https://drive.google.com/drive/folders/17CrMg_M6ZCV43hATKHRmWyuWUVaPHDfj?usp=sharing) que fue:

- Recolectado manualmente
- Organizado por clases de productos
- Etiquetado utilizando herramientas especializadas

El etiquetado permitió definir las clases que el modelo debía reconocer, siendo un paso clave para el entrenamiento.

---

## **Instalación**

Clonar el repositorio:

`git clone https://github.com/juandsandoval8/autocaja-yolo.git`


Instalar dependencias:

`pip install -r requirements.txt`

---

## **Uso**

Ejecutar el sistema:

`python proyecto.py`


El sistema iniciará la interfaz gráfica y comenzará la detección de productos en tiempo real

---

## **Arquitectura del sistema**

El proyecto está desarrollado bajo el paradigma de Programación Orientada a Objetos (POO), permitiendo una estructura modular y escalable.

### Componentes principales:

- Gestión de imágenes  
- Módulo de detección de productos  
- Interfaz gráfica de usuario  
- Lógica del sistema  

Cada componente está encapsulado en clases, facilitando el mantenimiento y la reutilización del código.

---

## **Entrenamiento del modelo**

El modelo de detección fue entrenado utilizando el dataset previamente etiquetado, ajustando parámetros para mejorar:

- Precisión  
- Rendimiento  
- Detección en tiempo real  

---

## **Pruebas y validación**

Se realizaron pruebas en distintos escenarios para:

- Verificar la precisión del modelo  
- Evaluar el rendimiento en condiciones reales  
- Validar la eficiencia del sistema completo  