from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import uuid

class AnalyzeRequest(BaseModel):
    sonar_project_key: str
    project_git_url: str
    project_git_branch: str = "master" # Opcional na requisição, valor default e 'master'

class IssueCategory(str, Enum):
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"
    RELIABILITY = "RELIABILITY"
    CODE_QUALITY = "CODE_QUALITY"
    BUG = "BUG"
    LOGIC = "LOGIC"
    OTHER = "OTHER"

class CodeIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: str  # Validaremos abaixo
    category: IssueCategory
    description: str
    file: str
    line: Optional[str] = None
    recommendation: str

    @field_validator('severity')
    def validate_severity(cls, validate):
        validate = validate.upper()
        if validate not in ['MINOR','LOW','MAJOR', 'MEDIUM', 'HIGH', 'CRITICAL', 'BLOCKER','INFO']:
            return 'MEDIUM'  # Valor padrão se inválido
        return validate
    
    @field_validator('category', mode='before')
    def validate_category(cls, validate):
        validate = validate.upper().strip()
        try:
            return IssueCategory(validate)
        except ValueError:
            # Mapeia categorias incorretas para valores válidos
            category_map = {
                'BUGS': IssueCategory.BUG,
                'LOGICS': IssueCategory.LOGIC,
                'QUALITY': IssueCategory.CODE_QUALITY
            }
            return category_map.get(validate, IssueCategory.OTHER)

class AnalysisResponse(BaseModel):
    analysis: List[CodeIssue] = []
    statistics: Optional[dict] = None
    
    # Método correto para serialização no Pydantic v2+
    def to_json(self, indent: Optional[int] = None) -> str:
        return self.model_dump_json(indent=indent)