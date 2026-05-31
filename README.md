# 🦆 GA2 Universal Extractor (GetAmped 2)

![Duck Labs](https://img.shields.io/badge/Developed%20by-Duck%20Labs-orange?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Game](https://img.shields.io/badge/Game-GetAmped%202-red?style=for-the-badge)

## 🚀 Visão Geral

Este é o **Extrator Universal de GA2**, uma ferramenta definitiva desenvolvida pela **Duck Labs** para descompilar e extrair recursos do jogo **GetAmped 2 (CyberStep)**. 

Diferente de extratores comuns, esta versão foi projetada para lidar com as diversas variações de segurança que o jogo utiliza, incluindo múltiplos esquemas de chaves XOR e diferentes formatos de cabeçalhos internos. Ela é capaz de processar desde scripts de lógica até os arquivos de classes Java do cliente.

---

## ✨ Recursos Principais

*   **🔍 Detecção Inteligente de XOR**: O script testa automaticamente as chaves conhecidas para o índice, eliminando a necessidade de configuração manual.
*   **📦 Suporte a Pacotes Híbridos**: Lida com arquivos que possuem cabeçalhos internos (`0x03 0x09`) e arquivos brutos (como `.class`).
*   **💾 Descompressão Automática**: Integra suporte a GZIP para extrair arquivos `.scm` e `.agi` já em formato legível.
*   **📂 Preservação de Estrutura**: Recria fielmente a árvore de diretórios original do jogo.
*   **🛠️ Filtros Avançados**: Extraia apenas o que você precisa (ex: apenas arquivos de áudio ou apenas scripts).

---

## 🔑 Especificações Técnicas (Chaves XOR)

O extrator trabalha com três chaves XOR principais identificadas nos arquivos do GetAmped 2:

| Chave XOR | Contexto de Uso | Exemplo de Arquivo |
| :--- | :--- | :--- |
| **`0xD5`** | Padrão global para a maioria dos recursos. | `1.ga2`, `resource.ga2` |
| **`0xB4`** | Específica para pacotes de classes Java. | `classes.ga2` |
| **`0x47`** | Utilizada em arquivos de dados de sistema. | `gs.ga2` |

> **Nota Técnica**: Para os dados individuais dos arquivos, o script calcula uma chave dinâmica baseada no offset: `(KEY_global + offset + 0xF9) & 0xFF`.

---

## ⚙️ Como Usar

### Comando Principal
Para extrair um arquivo completo, utilize a sintaxe abaixo:

```bash
python ga2_universal_extractor.py NOMEDOARQUIVO.GA2 --output ESCOLHANOMEDODESTINO
```

### Argumentos Disponíveis

| Argumento | Função |
| :--- | :--- |
| `--output <dir>` | Define a pasta de destino dos arquivos. |
| `--list` | Apenas lista os arquivos no terminal (sem extrair). |
| `--decompress` | Ativa a descompressão GZIP automática (recomendado para scripts). |
| `--filter .ext` | Extrai apenas arquivos com a extensão informada. |
| `--quiet` | Oculta as mensagens de progresso durante a extração. |

---

## 🛠️ Exemplos de Uso

**1. Extrair todas as classes do jogo:**
```bash
python ga2_universal_extractor.py classes.ga2 --output classes_extraidas
```

**2. Extrair e descompactar scripts de jogo:**
```bash
python ga2_universal_extractor.py 1.ga2 --output scripts --decompress
```

**3. Apenas listar o que há dentro de um arquivo:**
```bash
python ga2_universal_extractor.py resource.ga2 --list
```

---

## 📝 Créditos e Licença

Desenvolvido por **Duck Labs**. 
Este projeto foi criado para fins de estudo, preservação e modding ético do jogo GetAmped 2. 

---
*Powered by Duck Labs 🦆*
