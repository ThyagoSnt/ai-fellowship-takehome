export const EXAMPLE_LABEL = "carteira_oab"

export const EXAMPLE_SCHEMA = {
  nome: "Nome do profissional",
  inscricao: "Número de inscrição",
  seccional: "Seccional",
  subsecao: "Subseção",
  categoria: "Categoria (ADVOGADO/ADVOGADA/SUPLEMENTAR/ESTAGIARIO/ESTAGIARIA)",
  telefone_profissional: "Telefone do profissional",
  situacao: "Situação do profissional",
}

export const EXAMPLE_PDF_PATH = "./ai-fellowship-data/files/oab_1.pdf"

export const EXAMPLE_BATCH_JSON_PATH = "./ai-fellowship-data/dataset.json"
export const EXAMPLE_BATCH_PDFS_ROOT = "./ai-fellowship-data/files"

export const EXAMPLE_BATCH_MANIFEST = [
  {
    filename: "oab_1.pdf",
    label: EXAMPLE_LABEL,
    extraction_schema: EXAMPLE_SCHEMA,
  },
  {
    filename: "oab_2.pdf",
    label: EXAMPLE_LABEL,
    extraction_schema: EXAMPLE_SCHEMA,
  },
]
