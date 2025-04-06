import subprocess
import time
import socket

host, port = "127.0.0.1", 9001

blender_path = r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" 
blend_file = r"C:\Users\emanu\OneDrive\Desktop\untitled.blend"
server_script = r"C:\Users\emanu\ml4iot24\hand_tracking\blender_server.py"

# Avvia Blender con il server
subprocess.Popen([blender_path, blend_file, "--python", server_script])

# Attendi che Blender e il server siano pronti
time.sleep(20)

script_path = r"C:\Users\emanu\ml4iot24\hand_tracking\move_arm_R.py"

# Scrivi il codice direttamente nel file
code = """
import bpy
import math

# Nome della bone da muovere
bone_name = "upper_arm.R"  # Assicurati che il nome sia corretto

# Trova l'armatura che contiene questo bone
armature = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE' and bone_name in obj.pose.bones:
        armature = obj
        break

if armature:
    print(f"✅ Armatura trovata: {{armature.name}}")

    # **Ruota il bone**
    bone = armature.pose.bones.get(bone_name)
    print(bone)
    if bone:
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler[2] += math.radians(-30)  # Ruota di -30° su Z

        # **Forza l'aggiornamento della viewport**
        bpy.context.view_layer.update()

        print(f"✅ Ruotata {{bone_name}} di 30° su Z")
    else:
        print(f"❌ Errore: il boane '{{bone_name}}' non esiste nell'armatura.")

else:
    print("❌ Nessuna armatura trovata con questa bone!")
"""

with open(script_path, "w", encoding="utf-8") as file:
    file.write(code)  # Scrive il codice nel file

# Leggi il file e invia il contenuto al server
with open(script_path, "r", encoding="utf-8") as file:
    code_to_send = file.read()


for i in range(50):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    client.send(code.encode())
    print(client.recv(1024).decode())  # Output del server
client.close()
