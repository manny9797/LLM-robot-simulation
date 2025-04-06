import bpy
import math

# Nome della bone da muovere
bone_name = "thigh.L"  # Assicurati che il nome sia corretto

# Trova l'armatura che contiene questo bone
armature = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE' and bone_name in obj.pose.bones:
        armature = obj
        break

if armature:
    print(f"✅ Armatura trovata: {armature.name}")

    # **Ruota il bone**
    bone = armature.pose.bones.get(bone_name)
    print(bone)
    if bone:
        
        for i in range(2):
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler[0] += math.radians(-30)  # Ruota di -30° su X

            # **Forza l'aggiornamento della viewport**
            bpy.context.view_layer.update()

            print(f"✅ Ruotata {bone_name} di -30° su X")
    else:
        print(f"❌ Errore: il boane '{bone_name}' non esiste nell'armatura.")

else:
    print("❌ Nessuna armatura trovata con questa bone!")
