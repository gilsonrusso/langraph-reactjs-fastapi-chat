from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/sales", tags=["sales"])

class Sale(BaseModel):
    id: int
    product_name: str = Field(description="Nome do produto vendido")
    quantity: int = Field(description="Quantidade vendida")
    total_value: float = Field(description="Valor total da venda")

# Dados mockados
SALES_HISTORY = [
    {"id": 500, "product_name": "Laptop Pro", "quantity": 1, "total_value": 1200.0},
    {"id": 501, "product_name": "Mouse Sem Fio", "quantity": 2, "total_value": 50.0},
]

@router.get("/", response_model=List[Sale])
async def list_sales():
    """
    Recupera o histórico completo de transações e vendas realizadas.
    Utilize esta ferramenta para responder perguntas sobre o que foi vendido recentemente,
    volumes de vendas por produto ou para auditoria de transações.
    """
    return SALES_HISTORY

@router.get("/summary")
async def get_sales_summary():
    """
    Gera um relatório consolidado com o faturamento total (revenue) e o volume (count) de vendas.
    Esta é a ferramenta ideal para perguntas executivas sobre "Quanto vendemos no total?" 
    ou "Qual o desempenho financeiro atual?".
    """
    total = sum(sale["total_value"] for sale in SALES_HISTORY)
    return {"total_revenue": total, "total_sales_count": len(SALES_HISTORY)}
