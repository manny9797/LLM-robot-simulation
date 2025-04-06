import json
import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
import subprocess
import time
import socket
import subprocess
import time
import socket
from queue import Queue


class Dispatcher:
    def __init__(self):
        self.queue = Queue()
        self.visited_paths = set()  # Track (sender, receiver, message_id) tuples
        self.iteration_count = 0
        self.message_counter = 0  # Add a unique ID for each message

    def send_message(self, sender, receiver, message):
        """Aggiunge un messaggio alla coda con un ID univoco"""
        message_id = self.message_counter
        self.message_counter += 1
        self.queue.put((sender, receiver, message, self.iteration_count, message_id))

    def process_messages(self):
        """Processa i messaggi senza fermare l'esecuzione."""
        messages_processed = 0
        
        while not self.queue.empty():
            sender, receiver, message, iteration, message_id = self.queue.get()
            
            # Genera un identificatore univoco per questo specifico messaggio
            path_id = (
                sender.name if sender else "None", 
                receiver.name, 
                message_id
            )
            
            # Se questa esatta combinazione è già stata processata, salta
            if path_id in self.visited_paths:
                print(f"Messaggio già visitato: {sender.name if sender else 'None'} -> {receiver.name} (message_id {message_id})")
                continue
                
            # Segna questo messaggio specifico come visitato
            self.visited_paths.add(path_id)
            
            # Processa il messaggio
            receiver.process(message)
            messages_processed += 1
            
        # Incrementa l'iterazione solo se abbiamo processato qualcosa
        if messages_processed > 0:
            self.iteration_count += 1
            print(f"Completata iterazione {self.iteration_count-1}, {messages_processed} messaggi processati")



class SimpleNode:
    def __init__(self, name=None, model="gemini-2.0-flash", temperature=0.3, api_key=None, system_message=None, dispatcher=None):
        
        self.name = name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.next_nodes = []  # Lista di nodi successivi nella pipeline
        self.system_message = system_message
        self.dispatcher = dispatcher

    def add_next(self, node):
        """Collega questo nodo a un altro nodo successivo."""
        self.next_nodes.append(node)

    def process(self, input_text):
        """Processa il testo con l'LLM e propaga ai nodi successivi."""
        messages = [
            ("system", self.system_message),
            ("human", input_text)
        ]
        response = self.llm.invoke(messages)
        time.sleep(1)
        output_text = response.content  # Estrarre il testo generato

        print(f"🟢 Nodo: {self.name}")
        print(f"🔹 Input: {input_text}")
        print(f"🔸 Output: {output_text}\n")

        # Passa l'output ai nodi successivi
        for node in self.next_nodes:
            self.dispatcher.send_message(self, node, output_text)
            
              # Restituisce il risultato per utilizzi futuri

class PlanNode:
    def __init__(self, name=None, model="gemini-2.0-flash", temperature=0.3, api_key=None, system_message=None, dispatcher=None):
        
        self.name = name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.next_nodes = []  # Lista di nodi successivi nella pipeline
        self.system_message = system_message
        self.dispatcher = dispatcher

    def add_next(self, node):
        """Collega questo nodo a un altro nodo successivo."""
        self.next_nodes.append(node)

    def process(self, input_text):
        """Processa il testo con l'LLM e propaga ai nodi successivi."""
        messages = [
            ("system", self.system_message),
            ("human", input_text)
        ]
        response = self.llm.invoke(messages)
        output_text = response.content  # Estrarre il testo generato
        parts = output_text.split("```json")[1].split("```")[0].strip()
        print(f"🟢 Nodo: {self.name}")
        print(f"🔹 Input: {input_text}")
        print(f"🔸 Output: {output_text}\n")

        plan = json.loads(parts)
        
        print("STRUCTURED PLAN")
        print(plan)
        time.sleep(2)
        # Passa l'output ai nodi successivi
        for node in self.next_nodes:
            if node.name == "controller":
                self.dispatcher.send_message(self, node, plan)
    
class ChekNode:
    def __init__(self, name=None, model="gemini-2.0-flash", temperature=0.7, api_key=None, system_message=None, dispatcher=None):
        
        self.name = name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.next_nodes = []  # Lista di nodi successivi nella pipeline
        self.system_message = system_message
        self.step = 0
        self.dispatcher = dispatcher

    def add_next(self, node):
        """Collega questo nodo a un altro nodo successivo."""
        self.next_nodes.append(node)

    def process(self, input_text):
        """Processa il testo con l'LLM e propaga ai nodi successivi."""
        print(f"🟢 Nodo: {self.name}")
        
        plan = input_text["plan"]
        
        if self.step > len(plan) - 1:
            print(f"Piano completato, step {self.step}/{len(plan)}")
            return
        
        next_node, next_task = plan[self.step].split(":", 1)
        print(f"Esecuzione step {self.step+1}/{len(plan)}: {next_node}")
        
        # Incrementa lo step PRIMA di inviare il messaggio
        self.step += 1
        
        # Passa l'output ai nodi successivi
        for node in self.next_nodes:
            if node.name == next_node:
                print(f"Next node: {node.name}")
                self.dispatcher.send_message(self, node, {"task": next_task, "plan": plan})
        

class BoneNode:
    def __init__(self, name=None, model="gemini-2.0-flash", temperature=0.4, api_key=None, system_message=None, dispatcher=None):
        
        self.name = name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.next_nodes = []  # Lista di nodi successivi nella pipeline
        self.system_message = system_message
        self.dispatcher = dispatcher

    def add_next(self, node):
        """Collega questo nodo a un altro nodo successivo."""
        self.next_nodes.append(node)

    def process(self, input_text):

        task = input_text["task"]
        """Processa il testo con l'LLM e propaga ai nodi successivi."""

        messages = [
            ("system", self.system_message),
            ("human", task)
        ]

        response = self.llm.invoke(messages)
          # Estrarre il testo generato
        script_path = r"C:\Users\emanu\ml4iot24\hand_tracking\move_arm_R.py"

        full_text = response.content  # Estrarre il testo generato

        # Usa una regex per estrarre solo il codice Python
        match = re.search(r"```python\n(.*?)```", full_text, re.DOTALL)
        if match:
            code = match.group(1)  # Prende solo il codice tra i delimitatori
        else:
            raise ValueError("❌ Errore: il modello non ha generato codice Python valido!")

        with open(script_path, "w", encoding="utf-8") as file:
            file.write(code)  # Scrive il codice nel file

        # Leggi il file e invia il contenuto al server
        with open(script_path, "r", encoding="utf-8") as file:
            code_to_send = file.read()
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            client.send(code_to_send.encode())
            print(client.recv(1024).decode())  # Output del server

        time.sleep(2)
        print(f"🟢 Nodo: {self.name}")
        print(f"🔹 Input: {input_text}")
        print(f"🔸 Output: {code}\n")

        # Passa l'output ai nodi successivi
        for node in self.next_nodes:
            self.dispatcher.send_message(self, node, {"plan": input_text["plan"],
                          "code": code}) 
    
# ESEMPIO DI USO:
if __name__ == "__main__":

    host, port = "127.0.0.1", 9001

    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" 
    blend_file = r"C:\Users\emanu\OneDrive\Desktop\untitled.blend"
    server_script = r"C:\Users\emanu\ml4iot24\hand_tracking\blender_server.py"

    # Avvia Blender con il server
    subprocess.Popen([blender_path, blend_file, "--python", server_script])

    # Attendi che Blender e il server siano pronti
    time.sleep(20)
    os.environ["GOOGLE_API_KEY"] = "AIzaSyBAKMcYg1E3wpgM3VoCRWOyex6kS0LmMC4"

    dispatcher = Dispatcher()

    # Creiamo due nodi collegati tra loro
    head = SimpleNode(name="mind", system_message="You are an helpful assistant. You are an agent in a graph. Your specific role is the CEO. You have to instruct a planner on how to do a plan. In this case, the plans consist of different agents calls along with tasks. The tasks are related to movements of a body in blender. Specifically, the goal is to make an armature in blender able to move responding to user prompts. In this case, it is important to rotate some parts of the body of some degrees. Remember that we starts from an armature in blender that is in a default mode (arms down and legs normal down). You are able to instruct a planner on how to do a plan for moving body parts. Please, do not mention stuffs related to programming and blender (the plan nodes already know what they have to do from the instructions). The explanations should be short and very clear. Please, be clear and concise, do not add not useful stuffs. The instruction should be simple to move the body. Consider that the unique available body parts are the right arm, the left arm, the left leg and right leg. Please, if the request is not clear, ask for rephrasing the user. If you think the conversation should not proceed, say it.", dispatcher=dispatcher) 

    plan = PlanNode(name="Planner", system_message="""You are a planner of movements to move an armature with bones. You have to construct a plan list and a structured output. The available nodes to execute the task are: 
                    - right_arm (that is the right arm of the armature), 
                    - left_arm (that is the left arm of the armature)- 
    The plan should be done in the following form: 
    
    plan: ["node_name: instruction for node_1", "node_name: instruction for node_2", .. ]
                      
    The available nodes are:
    - right_arm: this node can be used to make actions on the right arm
    - left_arm: this node can be used to make actions on the left arm
    - right_leg: this node can be used to make actions on the right leg
    - left_leg: this node can be used to make actions on the left leg
    
    Please, include all the steps necessary to make a final movement, do not minimize steps. Remeber that you can put the same node twice or more in the plan. Try to put as much nodes as possible! We are trying to simulate a real movement and can be very complex.
    Basing on these informations, provide a structured json output in the form: 

    OUTPUT EXAMPLE: 
    {{
    "plan": [...]
    }}
                      ```
                                        
    !!! IMPORTANT !!! Return ONLY this output. Do not add stuffs. Remember to mark the json with ```json and ```            
    """, dispatcher=dispatcher) 

    check = ChekNode(name="controller", system_message="", dispatcher=dispatcher) 

    arm_R = BoneNode(name="right_arm", system_message="""You are an helpful assistant. You are a bone in an armature. Your task is to write a python code to make rotation of your corresponding bone in Blender. You are the right_arm. You should use only the bpy and the math library. Please, make sure that the movement generated fits the request. Here you can see an example of code to rotate your bone of 30 degrees (but you can use also other movements).
            EXAMPLE:
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
                            
                            for i in range(2):
                                bone.rotation_mode = 'XYZ'
                                bone.rotation_euler[2] += math.radians(20)  # Ruota di 20° su Z

                                # **Forza l'aggiornamento della viewport**
                                bpy.context.view_layer.update()

                                print(f"✅ Ruotata {{bone_name}} di 30° su Z")
                        else:
                            print(f"❌ Errore: il boane '{{bone_name}}' non esiste nell'armatura.")

                    else:
                        print("❌ Nessuna armatura trovata con questa bone!")
                     END EXAMPLE""", dispatcher=dispatcher)

    arm_L = BoneNode(name="left_arm", system_message="""You are an helpful assistant. You are a bone in an armature. Your task is to write a python code to make rotation of your corresponding bone in Blender. You are the left_arm. You should use only the bpy and the math library. Please, make sure that the movement generated fits the request. Here you can see an example of code to rotate your bone of 30 degrees (but you can use also other movements).
            EXAMPLE:
                    import bpy
                    import math

                    # Nome della bone da muovere
                    bone_name = "upper_arm.L"  # Assicurati che il nome sia corretto

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
                            
                            for i in range(2):
                                bone.rotation_mode = 'XYZ'
                                bone.rotation_euler[2] += math.radians(20)  # Ruota di 20° su Z

                                # **Forza l'aggiornamento della viewport**
                                bpy.context.view_layer.update()

                                print(f"✅ Ruotata {{bone_name}} di 30° su Z")
                        else:
                            print(f"❌ Errore: il boane '{{bone_name}}' non esiste nell'armatura.")

                    else:
                        print("❌ Nessuna armatura trovata con questa bone!")
                     END EXAMPLE""", dispatcher=dispatcher)

    leg_L = BoneNode(name="left_leg", system_message="""You are an helpful assistant. You are a bone in an armature. Your task is to write a python code to make rotation of your corresponding bone in Blender. You are the left_leg. You should use only the bpy and the math library. Please, make sure that the movement generated fits the request. Here you can see an example of code to rotate your bone of 30 degrees (but you can use also other movements).
            EXAMPLE:
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
                        print(f"✅ Armatura trovata: {{armature.name}}")

                        # **Ruota il bone**
                        bone = armature.pose.bones.get(bone_name)
                        print(bone)
                        if bone:
                            
                            for i in range(2):
                                bone.rotation_mode = 'XYZ'
                                bone.rotation_euler[2] += math.radians(20)  # Ruota di 20° su Z

                                # **Forza l'aggiornamento della viewport**
                                bpy.context.view_layer.update()

                                print(f"✅ Ruotata {{bone_name}} di 30° su Z")
                        else:
                            print(f"❌ Errore: il boane '{{bone_name}}' non esiste nell'armatura.")

                    else:
                        print("❌ Nessuna armatura trovata con questa bone!")
                     END EXAMPLE""", dispatcher=dispatcher)


    leg_R = BoneNode(name="right_leg", system_message="""You are an helpful assistant. You are a bone in an armature. Your task is to write a python code to make rotation of your corresponding bone in Blender. You are the right_leg. You should use only the bpy and the math library. Please, make sure that the movement generated fits the request. Here you can see an example of code to rotate your bone of 30 degrees (but you can use also other movements).
            EXAMPLE:
                    import bpy
                    import math

                    # Nome della bone da muovere
                    bone_name = "thigh.R"  # Assicurati che il nome sia corretto

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
                            
                            for i in range(2):
                                bone.rotation_mode = 'XYZ'
                                bone.rotation_euler[2] += math.radians(20)  # Ruota di 20° su Z

                                # **Forza l'aggiornamento della viewport**
                                bpy.context.view_layer.update()

                                print(f"✅ Ruotata {{bone_name}} di 30° su Z")
                        else:
                            print(f"❌ Errore: il boane '{{bone_name}}' non esiste nell'armatura.")

                    else:
                        print("❌ Nessuna armatura trovata con questa bone!")
                     END EXAMPLE""", dispatcher=dispatcher)
    
    # single edges thigh.L
    head.add_next(plan) 
    plan.add_next(check)
    arm_R.add_next(check)
    arm_L.add_next(check)
    leg_R.add_next(check)
    leg_L.add_next(check)

    # conditional edges
    check.add_next(arm_R)
    check.add_next(arm_L)    
    check.add_next(leg_R)
    check.add_next(leg_L)

    while True:
        user_prompt = input("💬 Scrivi il prompt per il LLM (o 'exit' per uscire): ")
        if user_prompt.lower() == "exit":
            break

        # Resetta lo stato del CheckNode
        check.step = 0  

        # Invia il primo messaggio al dispatcher
        dispatcher.send_message(None, head, user_prompt)

        # Avvia l'elaborazione dei messaggi (senza ricorsione!)
        dispatcher.process_messages()

