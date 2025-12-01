import sys
import os
import uuid
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load env vars
load_dotenv()

# Importamos supabase para crear el lead real primero
from supabase import create_client, Client
from app.agent_logic import create_agent_graph
from app.adapters.supabase_repo import SupabaseAdapter
from app.adapters.openai_llm import OpenAIAdapter

# Configurar Supabase para el test
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Instantiate adapters and agent
supabase_adapter = SupabaseAdapter(supabase)
openai_adapter = OpenAIAdapter()
agent_app = create_agent_graph(llm=openai_adapter, repo=supabase_adapter)

def create_test_campaign():
    """
    Crea una campaña de prueba en la BD.
    """
    print("Creating test campaign...")
    
    campaign_data = {
        "name": "Test Campaign - Automated",
        "status": "active"
    }
    
    try:
        response = supabase.table("campaigns").insert(campaign_data).execute()
        campaign_id = response.data[0]['id']
        print(f"✅ Campaign created successfully! ID: {campaign_id}")
        return campaign_id
    except Exception as e:
        print(f"❌ Error creating campaign: {e}")
        return None

def create_test_lead(campaign_id):
    """
    Crea un lead falso en la BD para poder probar el chat.
    """
    # Generamos un teléfono random para que no de error de duplicado si corres el test muchas veces
    random_phone = f"+346{uuid.uuid4().int.__str__()[:8]}" 
    
    print(f"Creating test lead with phone: {random_phone}...")
    
    lead_data = {
        "campaign_id": campaign_id,
        "name": "Usuario Test Automático",
        "phone": random_phone,
        "status": "new",
        "metadata": {"source": "test_script"}
    }
    
    try:
        response = supabase.table("leads").insert(lead_data).execute()
        # Supabase devuelve una lista de datos insertados
        lead_id = response.data[0]['id']
        print(f"✅ Lead created successfully! ID: {lead_id}")
        return lead_id, lead_data
    except Exception as e:
        print(f"❌ Error creating lead: {e}")
        return None, None

def run_real_simulation():
    print("--- 🚀 STARTING END-TO-END TEST ---")
    
    # PASO 1: Crear la campaña primero
    campaign_id = create_test_campaign()
    
    if not campaign_id:
        print("Stopping test due to campaign creation error.")
        return
    
    # PASO 2: Crear el Lead en DB
    lead_id, lead_data = create_test_lead(campaign_id)
    
    if not lead_id:
        print("Stopping test due to DB error.")
        return

    # AHORA SÍ tenemos un ID real para pasarle al agente
    lead_context = {"id": lead_id, "name": lead_data["name"]}
    
    messages_to_send = [
        "Hola, me interesa el servicio",
        "¿Es muy caro?",
        "Vale, quiero agendar una cita"
    ]
    
    conversation_history = []
    
    print("\n--- 💬 STARTING CONVERSATION ---")

    for i, msg_content in enumerate(messages_to_send):
        print(f"\n👤 User: '{msg_content}'")
        
        # Add user message to history
        conversation_history.append(HumanMessage(content=msg_content))
        
        # State actual
        initial_state = {
            "messages": conversation_history,
            "lead_context": lead_context,
            "intent": "unknown"
        }
        
        # Ejecutar el Cerebro (LangGraph)
        try:
            final_state = agent_app.invoke(initial_state)
            
            # Obtener respuesta
            reply_message = final_state["messages"][-1]
            reply_content = reply_message.content
            intent = final_state.get("intent")
            
            print(f"🤖 Agent (Intent: {intent}): {reply_content}")
            
            # Añadir respuesta del agente al historial para la siguiente vuelta
            conversation_history.append(reply_message)
            
        except Exception as e:
            print(f"❌ Error in agent execution: {e}")
            break

if __name__ == "__main__":
    run_real_simulation()