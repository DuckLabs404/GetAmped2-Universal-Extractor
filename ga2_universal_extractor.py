#!/usr/bin/env python3
"""
ga2_universal_extractor.py — Extrator Universal de arquivos .ga2 do GetAmped 2
=============================================================================
Identidade Visual: Duck Labs
"""

import struct
import os
import sys
import zlib
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Tenta importar colorama, mas define fallbacks se não estiver disponível
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

def print_banner():
    if HAS_COLORAMA:
        RED = Fore.RED + Style.BRIGHT
        YELLOW = Fore.YELLOW + Style.BRIGHT
        WHITE = Fore.WHITE + Style.BRIGHT
    else:
        RED = YELLOW = WHITE = ""

    # Parte 1: Duck Labs
    print(f"""{RED}
 _____             _     _           _          
|  __ \           | |   | |         | |         
| |  | |_   _  ___| | __| |     __ _| |__  ___  
| |  | | | | /  __| |/ /| |    / _` | '_ \/ __| 
| |__| | |_| | (__|   < | |___| (_| | |_) \__ \ 
|_____/ \__,_|\___|_|\_ |______\__,_|_.__/|___/""")
    
    # Parte 2: 404 (Amarelo, Branco, Amarelo)
    print(f"""
{YELLOW}            _  _     {WHITE}___  {YELLOW} _  _                        
{YELLOW}           | || |  {WHITE} / _ \ {YELLOW}| || |                       
{YELLOW}           | || |_ {WHITE}| | | |{YELLOW}| || |_                      
{YELLOW}           |__   _|{WHITE}| | | |{YELLOW}|__   _|                     
{YELLOW}              | |  {WHITE}| |_| |  {YELLOW} | |                       
{YELLOW}              |_|  {WHITE} \___/   {YELLOW} |_|                       
    """)
    time.sleep(0.5)

# ─── Constantes ───────────────────────────────────────────────────────────────

DEFAULT_INDEX_XOR_KEY = 0xD5   
CLASSES_INDEX_XOR_KEY = 0xB4   
GS_INDEX_XOR_KEY      = 0x47   # Nova chave para gs.ga2
INDEX_HEADER_SZ       = 21     
DATA_XOR_OFFSET       = 0xF9   
GZIP_MAGIC            = bytes([0x1F, 0x8B])
ENTRY_MAGIC           = bytes([0x03, 0x09])
JAVA_CLASS_MAGIC      = bytes([0xCA, 0xFE, 0xBA, 0xBE])

# ─── Estruturas de dados ──────────────────────────────────────────────────────

class FileEntry:
    __slots__ = ('path', 'offset', 'size', 'meta', 'xor_key')
    def __init__(self, path: str, offset: int, size: int, meta: Tuple[int, int, int, int], xor_key: int):
        self.path    = path
        self.offset  = offset
        self.size    = size
        self.meta    = meta
        self.xor_key = xor_key

# ─── Lógica de Decodificação ──────────────────────────────────────────────────

def decode_header(raw: bytes) -> Tuple[int, int, int, int]:
    if len(raw) < 8:
        raise ValueError("Arquivo muito pequeno para ser um .ga2 válido.")
    key        = struct.unpack_from('>I', raw, 0)[0]
    offset_enc = struct.unpack_from('>I', raw, 4)[0]
    offset_dec = offset_enc ^ key
    if offset_dec + 4 > len(raw):
        raise ValueError(f"OFFSET_DEC (0x{offset_dec:08x}) fora dos limites.")
    index_size  = struct.unpack_from('>I', raw, offset_dec)[0]
    index_start = offset_dec + 4
    return key, offset_dec, index_start, index_size

def detect_and_decode_index(raw: bytes, start: int, size: int) -> Tuple[bytes, int]:
    block = raw[start:start + size]
    # Tenta todas as chaves conhecidas
    for key in [DEFAULT_INDEX_XOR_KEY, CLASSES_INDEX_XOR_KEY, GS_INDEX_XOR_KEY]:
        decoded = bytes(b ^ key for b in block)
        if len(decoded) > INDEX_HEADER_SZ + 2:
            namesz = struct.unpack_from('>H', decoded, INDEX_HEADER_SZ)[0]
            if 0 < namesz < 256: 
                return decoded, key
    return bytes(b ^ DEFAULT_INDEX_XOR_KEY for b in block), DEFAULT_INDEX_XOR_KEY

def _parse_node(data: bytes, pos: int, path: str, key: int, entries: List[FileEntry]) -> int:
    if pos + 2 > len(data): return pos
    namesz = struct.unpack_from('>H', data, pos)[0]
    pos += 2
    if namesz == 0 or namesz > 512 or pos + namesz > len(data): return pos
    try:
        name = data[pos:pos + namesz].decode('utf-8', errors='replace')
    except:
        name = f"unknown_{pos}"
    pos += namesz
    if pos + 16 > len(data): return pos
    meta = struct.unpack_from('>IIII', data, pos)
    pos += 16
    if pos >= len(data): return pos
    node_type = data[pos]
    pos += 1
    if node_type != 0:
        if pos + 2 > len(data): return pos
        sub_count = struct.unpack_from('>H', data, pos)[0]
        pos += 2
        new_path = path + name + '/'
        for _ in range(sub_count):
            pos = _parse_node(data, pos, new_path, key, entries)
    else:
        if pos + 9 > len(data): return pos
        pos += 1 
        file_offset = struct.unpack_from('>I', data, pos)[0]; pos += 4
        file_size   = struct.unpack_from('>I', data, pos)[0]; pos += 4
        xor_key = (key + file_offset + DATA_XOR_OFFSET) & 0xFF
        entries.append(FileEntry(path + name, file_offset, file_size, meta, xor_key))
    return pos

def parse_entry_header(decoded: bytes) -> Dict:
    if len(decoded) < 10:
        return {'magic': b'', 'data_offset': 0, 'is_gzip': False}
    if decoded.startswith(JAVA_CLASS_MAGIC):
        return {'magic': JAVA_CLASS_MAGIC, 'data_offset': 0, 'is_gzip': False}
    magic = decoded[0:2]
    if magic != ENTRY_MAGIC:
        return {'magic': magic, 'data_offset': 0, 'is_gzip': False}
    path_len = decoded[6]
    path_start = 7
    if path_len == 0 or path_start + path_len > len(decoded):
        if len(decoded) > 7:
            path_len = decoded[7]
            path_start = 8
        else:
            return {'magic': magic, 'data_offset': 9, 'is_gzip': False}
    data_offset = path_start + path_len + 2
    is_gzip = (data_offset + 2 <= len(decoded) and decoded[data_offset:data_offset + 2] == GZIP_MAGIC)
    return {'magic': magic, 'data_offset': data_offset, 'is_gzip': is_gzip}

def decompress_gzip(data: bytes, offset: int) -> Optional[bytes]:
    payload = data[offset:]
    try:
        return zlib.decompress(payload, 16+zlib.MAX_WBITS)
    except:
        try:
            return zlib.decompress(payload, -zlib.MAX_WBITS)
        except:
            return None

def main():
    parser = argparse.ArgumentParser(description="GA2 Universal Extractor")
    parser.add_argument("input", help="Arquivo .ga2 de entrada")
    parser.add_argument("--output", default="output", help="Diretório de saída")
    parser.add_argument("--list", action="store_true", help="Apenas listar arquivos")
    parser.add_argument("--decompress", action="store_true", help="Descomprimir GZIP automaticamente")
    parser.add_argument("--filter", help="Filtrar por extensão (ex: .scm)")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso")
    args = parser.parse_args()

    if not args.quiet:
        print_banner()

    if not os.path.exists(args.input):
        print(f"Erro: Arquivo '{args.input}' não encontrado.")
        return

    if not args.quiet: print(f"Lendo '{args.input}'...")
    with open(args.input, 'rb') as f: raw = f.read()

    try:
        key, _, i_start, i_size = decode_header(raw)
        idx_data, used_xor = detect_and_decode_index(raw, i_start, i_size)
        if not args.quiet: print(f"  Chave Global: 0x{key:08x} | Chave Índice: 0x{used_xor:02x}")
        
        entries = []
        sys.setrecursionlimit(200000)
        pos = INDEX_HEADER_SZ
        while pos < len(idx_data):
            new_pos = _parse_node(idx_data, pos, '', key, entries)
            if new_pos <= pos: break # Evitar loop infinito
            pos = new_pos
        
        if args.list:
            print(f"\n{'#':<7} {'Offset':<12} {'Tamanho':<10} {'Caminho'}")
            print("-" * 80)
            for i, e in enumerate(entries):
                print(f"{i:<7} 0x{e.offset:08x} {e.size:<10} {e.path}")
            print(f"\nTotal: {len(entries)} arquivo(s)")
            return

        if not args.quiet: print(f"Extraindo {len(entries)} arquivos para '{args.output}'...")
        success = 0
        for entry in entries:
            if args.filter and not entry.path.lower().endswith(args.filter.lower()):
                continue
            
            chunk = raw[entry.offset : entry.offset + entry.size]
            decoded = bytes(b ^ entry.xor_key for b in chunk)
            hdr = parse_entry_header(decoded)
            
            content = decoded[hdr['data_offset']:]
            if args.decompress and hdr['is_gzip']:
                decomp = decompress_gzip(decoded, hdr['data_offset'])
                if decomp: content = decomp
            
            out_path = Path(args.output) / entry.path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(content)
            success += 1
            if not args.quiet and success % 100 == 0:
                print(f"  Progresso: {success}/{len(entries)}", end='\r')

        if not args.quiet: print(f"\nConcluído! {success} arquivo(s) extraídos.")

    except Exception as e:
        print(f"\nErro durante o processamento: {e}")

if __name__ == "__main__":
    main()
