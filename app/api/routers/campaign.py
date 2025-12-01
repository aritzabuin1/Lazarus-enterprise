from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from io import BytesIO
from app.tasks.chat_tasks import process_chat
from app.adapters.supabase_repo import SupabaseAdapter
from app.database import supabase
from app.domain.models import LeadCreate, LeadStatus
from app.logger import logger

router = APIRouter(prefix="/campaign", tags=["campaign"])

@router.post("/upload")
async def upload_campaign(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        contents = await file.read()
        # Read as string to preserve phone numbers (leading zeros, + sign)
        df = pd.read_csv(BytesIO(contents), dtype=str)
        
        # Normalize columns to lowercase
        df.columns = df.columns.str.lower()
        
        required_columns = {'name', 'phone'}
        if not required_columns.issubset(df.columns):
             raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_columns}")

        adapter = SupabaseAdapter(supabase)
        leads_queued = 0
        
        # Create a new campaign for this upload
        # We use direct supabase client here as we don't have a CampaignRepo yet
        campaign_name = f"Upload: {file.filename}"
        camp_res = supabase.table("campaigns").insert({"name": campaign_name, "status": "active"}).execute()
        if not camp_res.data:
            raise HTTPException(status_code=500, detail="Failed to create campaign")
        
        campaign_id = camp_res.data[0]['id']
        logger.info(f"Created campaign {campaign_id} for upload")

        with open("debug_campaign.txt", "w") as f:
            f.write(f"DataFrame shape: {df.shape}\n")
            f.write(f"DataFrame columns: {df.columns}\n")
            f.write(f"DataFrame head:\n{df.head()}\n")

        for _, row in df.iterrows():
            try:
                name = str(row.get('name', ''))
                phone = str(row.get('phone', ''))
                
                # Basic cleanup
                if not phone or phone == 'nan':
                    continue

                # 1. Save to Supabase
                lead_in = LeadCreate(
                    phone=phone,
                    name=name,
                    campaign_id=campaign_id,
                    status=LeadStatus.NEW
                )
                
                lead = adapter.create_lead(lead_in)
                lead_id = lead.id
                
                # 2. Trigger Agent
                # Initial message to kickstart the conversation
                initial_msg = "Hola, ¿en qué puedo ayudarte?"
                
                process_chat.delay(initial_msg, {"id": lead_id, "name": name})
                leads_queued += 1
                
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                logger.error(f"Failed to process row: {e}")
                continue

        return {
            "status": "success", 
            "leads_queued": leads_queued, 
            "campaign_id": campaign_id,
            "message": "Campaign uploaded and processing started"
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
