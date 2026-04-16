import os
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop

def convertir_a_vertical(input_file, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    clip = VideoFileClip(input_file)
    w, h = clip.size
    
    # Calculamos el ancho para 9:16 (vertical) centrado
    target_width = h * 9 / 16
    x_center = w / 2
    
    clip_vertical = crop(clip, x_center=x_center, y_center=h/2, 
                         width=target_width, height=h)
    
    # Dividir en partes de 30 segundos
    duracion_segmento = 30
    total_segments = int(clip.duration // duracion_segmento)

    for i in range(total_segments):
        start = i * duracion_segmento
        end = (i + 1) * duracion_segmento
        nuevo_clip = clip_vertical.subclip(start, end)
        
        nombre_salida = f"{output_folder}/short_{i+1}.mp4"
        nuevo_clip.write_videofile(nombre_salida, codec="libx264", audio_codec="aac", fps=30, preset="ultrafast")

    clip.close()
    print("--- ¡Proceso terminado con éxito! ---")
