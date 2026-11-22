import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# DEFINICIÓN DE LA FUNCIÓN DE EVALUACIÓN
# ==========================================
def f1(x):
    """Función de aptitud (Fitness) a maximizar."""
    return (np.sin(5 * np.pi * x))**6 * np.exp(-2 * np.log(2) * ((x - 0.1) / 0.8)**2)

# ==========================================
# PASOS DEL ALGORITMO GENÉTICO SIMPLE (SGA)
# ==========================================

# 1. Inicia Población Inicial aleatoriamente
def iniciar_poblacion(tam_poblacion, x_min=0.0, x_max=1.0):
    """Genera n individuos dentro del dominio real [x_min, x_max]."""
    return np.random.uniform(x_min, x_max, size=tam_poblacion)

# 2 y 7. Evalúa (Pob)
def evaluar_poblacion(poblacion):
    """Calcula el valor de aptitud (fitness) para cada individuo."""
    return f1(poblacion)

# 4. Selección (Pob) - Selección por Ruleta (Proporcional al Fitness)
def seleccion_ruleta(poblacion, aptitudes):
    """Selecciona individuos basados en su probabilidad proporcional de aptitud."""
    # Previene división por cero en aptitudes nulas
    probabilidades = aptitudes / np.sum(aptitudes)
    indices_seleccionados = np.random.choice(len(poblacion), size=len(poblacion), p=probabilidades)
    return poblacion[indices_seleccionados]

# 5. Reproducción (Cruce / Recombinación)
def reproduccion(poblacion, prob_cruce=0.8):
    """Aplica cruce aritmético entre pares de padres."""
    descendencia = []
    n = len(poblacion)
    
    for i in range(0, n, 2):
        padre1 = poblacion[i]
        padre2 = poblacion[(i + 1) % n]  # Conecta el último con el primero si n es impar
        
        if np.random.rand() < prob_cruce:
            # Cruce aritmético usando un factor alpha estocástico
            alpha = np.random.rand()
            hijo1 = alpha * padre1 + (1 - alpha) * padre2
            hijo2 = (1 - alpha) * padre1 + alpha * padre2
        else:
            hijo1, hijo2 = padre1, padre2
            
        descendencia.extend([hijo1, hijo2])
        
    return np.array(descendencia[:n])

# 6. Mutación (Pob)
def mutacion(poblacion, prob_mutacion=0.1, x_min=0.0, x_max=1.0):
    """Aplica una pequeña perturbación gaussiana a los individuos."""
    poblacion_mutada = poblacion.copy()
    for i in range(len(poblacion_mutada)):
        if np.random.rand() < prob_mutacion:
            # Perturbación aleatoria gaussiana
            ruido = np.random.normal(0, 0.05)
            poblacion_mutada[i] += ruido
            # Mantener al individuo dentro de los límites [x_min, x_max]
            poblacion_mutada[i] = np.clip(poblacion_mutada[i], x_min, x_max)
            
    return poblacion_mutada

# ==========================================
# ESTRUCTURA PRINCIPAL DEL ALGORITMO (BEGIN - FIN)
# ==========================================
def algoritmo_evolutivo():
    # Parámetros del Algoritmo
    TAM_POBLACION = 30
    MAX_GENERACIONES = 50
    PROB_CRUCE = 0.85
    PROB_MUTACION = 0.1
    
    # Begin
    print("Iniciando Algoritmo Evolutivo...\n")
    
    # 1. Inicia Pob inicial aleatoriamente
    poblacion = iniciar_poblacion(TAM_POBLACION)
    
    # 2. Evalúa (Pob)
    aptitudes = evaluar_poblacion(poblacion)
    
    generacion = 0
    
    # 3. Mientras no_se_cumpla hacer (Criterio de parada: Número máximo de generaciones)
    while generacion < MAX_GENERACIONES:
        # 4. Selección (Pob)
        poblacion_seleccionada = seleccion_ruleta(poblacion, aptitudes)
        
        # 5. Reproducción (Pob)
        poblacion_cruzada = reproduccion(poblacion_seleccionada, PROB_CRUCE)
        
        # 6. Mutación (Pob)
        poblacion = mutacion(poblacion_cruzada, PROB_MUTACION)
        
        # 7. Evalúa (Pob)
        aptitudes = evaluar_poblacion(poblacion)
        
        # Reporte de avance
        mejor_fit = np.max(aptitudes)
        print(f"Gen {generacion + 1:02d} | Mejor Fitness: {mejor_fit:.6f} | Mejor x: {poblacion[np.argmax(aptitudes)]:.6f}")
        
        generacion += 1
    # 8. Fin Mientras
    
    # 9. Obtiene Pob
    idx_mejor = np.argmax(aptitudes)
    mejor_x = poblacion[idx_mejor]
    mejor_f = aptitudes[idx_mejor]
    
    print("\n-------------------------------------------")
    print(f"Resultado final:")
    print(f"Mejor individuo x*: {mejor_x:.6f}")
    print(f"Valor máximo f1(x*): {mejor_f:.6f}")
    print("-------------------------------------------")
    
    return poblacion, mejor_x, mejor_f
    # 10. Fin

# Ejecución del algoritmo
poblacion_final, mejor_x, mejor_f = algoritmo_evolutivo()