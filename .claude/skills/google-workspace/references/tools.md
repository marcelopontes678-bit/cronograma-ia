# Catálogo de ferramentas do workspace-mcp

Nomes conforme registrados pelo servidor. No Claude Code chegam com o prefixo do
servidor: `mcp__google_workspace__<nome>`.

Quais aparecem depende de `--tool-tier` / `--tools` / `--permissions` no `.mcp.json`.
A lista abaixo é a do tier `complete`; com `core` (padrão deste repositório) só um
subconjunto é registrado. Para ver o que está ativo de fato, consulte as ferramentas
disponíveis na sessão.

Quase todas aceitam `user_google_email`. Defina `USER_GOOGLE_EMAIL` para omiti-lo.

## Gmail (`--tools gmail`)

| Ferramenta | O que faz |
|---|---|
| `search_gmail_messages` | Busca mensagens com a sintaxe de busca do Gmail |
| `get_gmail_message_content` | Conteúdo de uma mensagem |
| `get_gmail_messages_content_batch` | Conteúdo de várias mensagens de uma vez |
| `get_gmail_thread_content` | Conteúdo de uma thread |
| `get_gmail_threads_content_batch` | Conteúdo de várias threads |
| `get_gmail_attachment_content` | Baixa/lê um anexo |
| `send_gmail_message` | **Envia e-mail** — confirme com o usuário antes |
| `draft_gmail_message` | Cria rascunho (alternativa segura ao envio direto) |
| `list_gmail_labels` / `manage_gmail_label` | Lista e cria/edita/remove labels |
| `modify_gmail_message_labels` / `batch_modify_gmail_message_labels` | Aplica ou remove labels |
| `list_gmail_filters` / `manage_gmail_filter` | Lista e gerencia filtros |

Níveis de permissão do Gmail (cumulativos): `readonly` → `organize` → `drafts` →
`send` → `full`.

## Drive (`--tools drive`)

| Ferramenta | O que faz |
|---|---|
| `search_drive_files` | Busca arquivos (resolva nome → file ID aqui) |
| `list_drive_items` | Lista itens de uma pasta |
| `get_drive_file_content` | Lê o conteúdo de um arquivo |
| `get_drive_file_download_url` | URL de download |
| `create_drive_file` / `create_drive_folder` | Cria arquivo/pasta |
| `update_drive_file` / `copy_drive_file` | Atualiza / copia |
| `import_to_google_doc` / `import_to_google_sheets` / `import_to_google_slides` | Converte um upload em documento nativo |
| `get_drive_file_permissions` / `set_drive_file_permissions` / `manage_drive_access` | **Compartilhamento** — ação externa, confirme antes |
| `get_drive_shareable_link` / `check_drive_file_public_access` | Link de compartilhamento e checagem de exposição pública |

## Calendar (`--tools calendar`)

| Ferramenta | O que faz |
|---|---|
| `list_calendars` / `create_calendar` | Lista e cria agendas |
| `get_events` | Lista eventos de um intervalo |
| `manage_event` | Cria, edita e remove eventos — **convida participantes**, confirme antes |
| `query_freebusy` | Consulta disponibilidade |
| `manage_focus_time` / `manage_out_of_office` | Blocos de foco e ausência |

## Docs (`--tools docs`)

| Ferramenta | O que faz |
|---|---|
| `search_docs` / `list_docs_in_folder` | Localiza documentos |
| `get_doc_content` / `get_doc_as_markdown` | Lê o documento |
| `inspect_doc_structure` | Estrutura/índices — use antes de edições posicionais |
| `create_doc` | Cria documento |
| `modify_doc_text` / `find_and_replace_doc` / `batch_update_doc` | Edita texto |
| `insert_doc_elements` / `insert_doc_image` / `create_table_with_data` | Insere elementos, imagens e tabelas |
| `update_paragraph_style` / `update_doc_headers_footers` | Formatação, cabeçalho e rodapé |
| `manage_doc_tab` | Abas do documento |
| `export_doc_to_pdf` | Exporta para PDF |

## Sheets (`--tools sheets`)

| Ferramenta | O que faz |
|---|---|
| `list_spreadsheets` / `get_spreadsheet_info` | Localiza e inspeciona planilhas |
| `create_spreadsheet` / `create_sheet` | Cria planilha / aba |
| `read_sheet_values` | Lê um intervalo |
| `modify_sheet_values` / `append_table_rows` | Escreve e acrescenta linhas |
| `move_sheet_rows` / `resize_sheet_dimensions` | Move linhas, redimensiona |
| `format_sheet_range` / `manage_conditional_formatting` | Formatação |
| `list_sheet_tables` | Lista tabelas detectadas |

## Slides (`--tools slides`)

| Ferramenta | O que faz |
|---|---|
| `create_presentation` / `get_presentation` | Cria e lê apresentações |
| `get_page` / `get_page_thumbnail` | Slide individual e miniatura |
| `batch_update_presentation` | Edições em lote |

## Forms (`--tools forms`)

| Ferramenta | O que faz |
|---|---|
| `create_form` / `get_form` / `batch_update_form` | Cria, lê e edita formulários |
| `list_form_responses` / `get_form_response` | Respostas |
| `set_publish_settings` | Publicação — ação externa, confirme antes |

## Tasks (`--tools tasks`)

| Ferramenta | O que faz |
|---|---|
| `list_task_lists` / `get_task_list` / `manage_task_list` | Listas de tarefas |
| `list_tasks` / `get_task` / `manage_task` | Tarefas |

## Chat (`--tools chat`)

Requer configuração extra da Chat API (veja `setup-google-cloud.md`).

| Ferramenta | O que faz |
|---|---|
| `list_spaces` / `get_messages` / `search_messages` | Leitura |
| `send_message` | **Posta mensagem** — ação externa, confirme antes |
| `create_reaction` / `download_chat_attachment` | Reações e anexos |

## Contacts (`--tools contacts`)

| Ferramenta | O que faz |
|---|---|
| `list_contacts` / `search_contacts` / `get_contact` | Leitura |
| `manage_contact` / `manage_contacts_batch` | Cria, edita e remove contatos |
| `list_contact_groups` / `get_contact_group` / `manage_contact_group` | Grupos |

## Custom Search (`--tools search`)

Requer `GOOGLE_PSE_API_KEY` e `GOOGLE_PSE_ENGINE_ID`.

| Ferramenta | O que faz |
|---|---|
| `search_custom` | Busca via Programmable Search Engine |
| `get_search_engine_info` | Metadados do engine |
