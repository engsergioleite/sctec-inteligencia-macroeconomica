# ===== Pipeline completo: extração -> transformação -> carga =====
import sys

from src.carga import carregar
from src.extracao import extrair_todas
from src.transformacao import transformar

# ===== Execução das etapas =====
if __name__ == "__main__":
    extrair_todas()
    transformar()

    # Carga opcional: "python pipeline.py --sem-carga" pula o Supabase
    if "--sem-carga" not in sys.argv:
        carregar()
