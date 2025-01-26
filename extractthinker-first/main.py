import os
from typing import Any
from extract_thinker import (
    Extractor, LLM, Classification, Contract, DocumentLoaderPyPdf
)

#=========================
#   UTILS
#=========================
class CVContract(Contract):
    name: str
    email: str
    technical_skills: list[str]
    certifications: list[str]
    phone: str
    address: str | None
    summary: str
    experience: Any
    education: Any

class JobOfferContract(Contract):
    company_name: str
    position: str
    base_salary: str
    start_date: str

#=========================
#   CONSTANTS
#=========================
cv_candidate_path = os.path.join("files", "CV_Candidate.pdf")
job_offer_path = os.path.join("files", "Job_Offer.pdf")

# Initialize document loader
## document_loader = DocumentLoaderMarkItDown()
document_loader = DocumentLoaderPyPdf()

# Initialize the extractor
extractor = Extractor()
extractor.load_document_loader(document_loader)

# Load custom LLM via Ollama
llm = LLM('ollama/llama3:latest')
extractor.load_llm(llm)
## extractor.load_llm("gpt-4o-mini")  # set ENV key and then you can use OpenAI directly

classifications = [
    Classification(
        name="Candidate Resume",
        description="A document containing a candidate's personal, professional, and educational background, highlighting their skills, experiences, and qualifications.",
        contract=CVContract,
    ),
    Classification(
        name="Job Offer Document",
        description="A formal document outlining the details of a job offer, including role, compensation, and terms of employment.",
    ),
]

#=========================
#   MAIN
#=========================
print("Document Loader")
print(extractor.get_document_loader_for_file(cv_candidate_path))

print("Loaded Content")
print(extractor.document_loader.load(cv_candidate_path))

# Extract features from document
print("Basic Extraction of Fields")
## cv_features: CVContract = extractor.extract(cv_candidate_path, CVContract)
## print(cv_features)
jb_features: JobOfferContract = extractor.extract(job_offer_path, JobOfferContract)
print(jb_features)

"""
# Classify document
print("Classification")
classification: CVContract | None = extractor.classify(
    cv_candidate_path,
    [classifications[0]],
)
print(classification)
print(classification.confidence)
classification: CVContract | JobOfferContract = extractor.classify(
    job_offer_path,
    classifications,
    vision=False,  # set to True for image-based classification
)
print(classification)
print(classification.confidence)

# Code that doesn't work: https://github.com/enoch3712/ExtractThinker/blob/main/extract_thinker/extractor.py#L519
"""
