# app/services/s3_service.py
import boto3
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# DEBUG: Verificar que las variables existen
print("=== DEBUG S3 SERVICE ===")
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
session_token = os.getenv("AWS_SESSION_TOKEN")
region = os.getenv("AWS_REGION")
bucket = os.getenv("AWS_S3_BUCKET_NAME")

print(f"AWS_ACCESS_KEY_ID: {access_key[:10] if access_key else 'NO EXISTE'}...")
print(f"AWS_SECRET_KEY: {secret_key[:10] if secret_key else 'NO EXISTE'}...")
print(f"AWS_SESSION_TOKEN: {'EXISTE' if session_token else 'NO EXISTE'}")
print(f"AWS_REGION: {region}")
print(f"AWS_S3_BUCKET_NAME: {bucket}")
print("========================")

# Verificar que todas las credenciales existen
if not all([access_key, secret_key, bucket]):
    print("❌ FALTAN VARIABLES DE ENTORNO. Revisa tu archivo .env")
    print("El archivo .env debe estar en:", os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    s3_client = None  # 👈 Definir como None si faltan
else:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,  
        region_name=region
    )
    print("✅ S3 Client creado correctamente")

BUCKET_NAME = bucket

def upload_image_to_s3(image_bytes: bytes, folder: str = "alertas") -> str:
    try:
        if s3_client is None:  # 👈 Verificar si el cliente existe
            print("❌ S3 Client no inicializado")
            return None
            
        if not BUCKET_NAME:
            print("❌ BUCKET_NAME no configurado")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{folder}/{timestamp}_{unique_id}.jpg"
        
        s3_client.put_object(
            Body=image_bytes,
            Bucket=BUCKET_NAME,
            Key=filename,
            ContentType='image/jpeg'
        )
        
        url = f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{filename}"
        print(f"✅ Imagen subida a S3: {url}")
        return url
    except Exception as e:
        print(f"❌ Error subiendo a S3: {e}")
        return None