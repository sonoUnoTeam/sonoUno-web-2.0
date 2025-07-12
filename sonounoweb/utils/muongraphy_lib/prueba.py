
import base64
from utils.muongraphy_lib.muon_bash import process_files

def save_base64_image(base64_str, filename):
    with open(filename, "wb") as f:
        f.write(base64.b64decode(base64_str))

def main():
    # Definir las variables directamente
    file_type = 'csv'
    directory = r'C:\Users\Gonza\Downloads\archivos_ejemplo\Muongraphy-1'
    plot_flag = True
    target_file = '5565547_19009797(line).csv'
    
    # Llamar a la función process_files con las variables definidas
    try:
        plots_base64, sounds = process_files(directory, target_file, file_type, plot_flag)
        if plots_base64 is None or sounds is None:
            raise ValueError("Returned None from process_files")
        
        # Guardar las imágenes en archivos
        for key, value in plots_base64.items():
            save_base64_image(value, f"{key}.png")
            print(f"Saved {key}.png")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()