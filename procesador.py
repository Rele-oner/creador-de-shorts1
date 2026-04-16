import os
import numpy as np
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop
from scipy.ndimage import gaussian_filter

def calcular_centro_optimo(clip, target_width, target_height):
    """Calcula el centro horizontal óptimo basado en la 'atención' visual"""
    print("🧠 Analizando la escena para el enfoque automático (Auto-Reframe)...")
    try:
        # Cogemos unos fotogramas clave para analizar (no todos para ir rápido)
        frames_to_check = 10
        total_frames = int(clip.duration * clip.fps)
        step = max(1, total_frames // frames_to_check)
        
        centers = []
        # Parámetros de la ventana de visión 9:16
        w_source, h_source = clip.size
        
        for i in range(0, total_frames, step):
            frame = clip.get_frame(i / clip.fps)
            
            # Convertimos a escala de grises para detectar contraste/bordes
            frame_gray = np.mean(frame, axis=2)
            
            # Aplicamos un desenfoque suave para eliminar ruido (suaviza el movimiento)
            frame_blurred = gaussian_filter(frame_gray, sigma=5)
            
            # Buscamos las zonas con más detalles (las letras del karaoke tendrán mucho contraste)
            gx, gy = np.gradient(frame_blurred)
            edge_strength = gx**2 + gy**2
            
            # Buscamos el "centro de masa" horizontal de esta actividad
            horizontal_profile = np.sum(edge_strength, axis=0)
            
            # Si hay actividad, calculamos su centro
            if np.sum(horizontal_profile) > 0:
                current_center = np.average(np.arange(w_source), weights=horizontal_profile)
                
                # Limitamos el centro para no salirnos de los bordes del video original
                margin = target_width / 2
                current_center = np.clip(current_center, margin, w_source - margin)
                centers.append(current_center)
        
        # Si no detectamos nada claro, usamos el centro puro
        if not centers:
            return w_source / 2
        
        # Devolvemos la media de todos los centros detectados
        return np.mean(centers)
        
    except Exception as e:
        print(f"⚠️ Error en Auto-Reframe, usando centro puro. Info: {e}")
        return clip.size[0] / 2

def convertir_a_vertical(input_file, output_folder):
    """Convierte un video horizontal a vertical con Auto-Reframe y ALTA CALIDAD"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Cargamos el video original
    print(f"🎬 Cargando video original: {input_file}")
    clip = VideoFileClip(input_file)
    w_source, h_source = clip.size
    
    # Parámetros objetivo (Vertical 9:16)
    target_width = h_source * 9 / 16
    target_height = h_source
    
    # 1. Calculamos el centro óptimo (Auto-Reframe)
    x_center_optimo = calcular_centro_optimo(clip, target_width, target_height)
    
    # 2. Aplicamos el recorte
    print(f"✂️ Aplicando recorte inteligente centrado en x={int(x_center_optimo)}px...")
    clip_vertical = crop(clip, x_center=x_center_optimo, y_center=h_source/2, 
                         width=target_width, height=target_height)
    
    # 3. Dividimos en Shorts de 30 segs
    duracion_segmento = 30
    total_segments = int(clip.duration // duracion_segmento)

    print(f"📼 Generando {total_segments} shorts de alta calidad...")
    
    # Configuración de calidad profesional (Más lento, pero sin pixelado)
    # pix_fmt yuv420p arregla el error de Windows
    # crf=18 da calidad profesional
    params = ["-pix_fmt", "yuv420p", "-crf", "18"]
    
    for i in range(total_segments):
        start = i * duracion_segmento
        end = min((i + 1) * duracion_segmento, clip.duration)
        nuevo_clip = clip_vertical.subclip(start, end)
        
        nombre_salida = f"{output_folder}/short_HQ_{i+1}.mp4"
        print(f"👉 Procesando Parte {i+1}...")
        
        # Escribimos el archivo. Tardará más, pero la calidad es TOP.
        # Quitamos remove_temp=True para evitar errores tontos con el audio
        nuevo_clip.write_videofile(nombre_salida, 
                                codec="libx264", 
                                audio_codec="aac", 
                                fps=30, 
                                preset="slow", 
                                ffmpeg_params=params,
                                logger=None) # logger=None limpia la pantalla de Colab

    clip.close()
    print("--- ✅ ¡Proceso de ALTA CALIDAD terminado con éxito! ---")
